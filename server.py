from typing import List, Tuple, Optional
import numpy as np
from pathlib import Path

import flwr as fl
from flwr.common import Metrics

from dataclasses import dataclass
from logging import INFO
from typing import Dict, Optional, Tuple, Union

from flwr.common import GRPC_MAX_MESSAGE_LENGTH
from flwr.common.logger import log
from flwr.server.client_manager import ClientManager, SimpleClientManager
from flwr.server.grpc_server.grpc_server import start_grpc_server
from flwr.server.history import History
from flwr.server.server import Server
from flwr.server.strategy import FedAvg, Strategy

# Set Server Address(Port)
DEFAULT_SERVER_ADDRESS = 'localhost:' + input("Enter server PORT:")

# 


# Define  Configuration
class Config:
    """Internal Flower server config.
    """
    num_rounds: int = 1
    round_timeout: Optional[float] = None

# Define start_server
def start_server(  # pylint: disable=too-many-arguments
    server_address: str = DEFAULT_SERVER_ADDRESS,
    server: Optional[Server] = None,
    config: Optional[Dict[str, Union[int, Optional[float]]]] = None,
    strategy: Optional[Strategy] = None,
    client_manager: Optional[ClientManager] = None,
    grpc_max_message_length: int = GRPC_MAX_MESSAGE_LENGTH,
    force_final_distributed_eval: bool = False,
    certificates: Optional[Tuple[bytes, bytes, bytes]] = None,
) -> History:
    """Start a Flower server using the gRPC transport layer.

    Arguments
    ---------
        server_address: Optional[str] (default: `"[::]:8080"`). The IPv6
            address of the server.
        server: Optional[flwr.server.Server] (default: None). An implementation
            of the abstract base class `flwr.server.Server`. If no instance is
            provided, then `start_server` will create one.
        config: Optional[Dict[str, Union[int, Optional[float]]]] (default: None).
            Currently supported values are `num_rounds` (int, default: 1) and
            `round_timeout` in seconds (float, default: None), so a full configuration
            object instructing the server to perform three rounds of federated
            learning with a round timeout of 10min looks like the following:
            `{"num_rounds": 3, "round_timeout": 600.0}`.
        strategy: Optional[flwr.server.Strategy] (default: None). An
            implementation of the abstract base class `flwr.server.Strategy`.
            If no strategy is provided, then `start_server` will use
            `flwr.server.strategy.FedAvg`.
        client_manager: Optional[flwr.server.ClientManager] (default: None)
            An implementation of the abstract base class `flwr.server.ClientManager`.
            If no implementation is provided, then `start_server` will use
            `flwr.server.client_manager.SimpleClientManager`.
        grpc_max_message_length: int (default: 536_870_912, this equals 512MB).
            The maximum length of gRPC messages that can be exchanged with the
            Flower clients. The default should be sufficient for most models.
            Users who train very large models might need to increase this
            value. Note that the Flower clients need to be started with the
            same value (see `flwr.client.start_client`), otherwise clients will
            not know about the increased limit and block larger messages.
        force_final_distributed_eval: bool (default: False).
            Forces a distributed evaluation to occur after the last training
            epoch when enabled.
        certificates : Tuple[bytes, bytes, bytes] (default: None)
            Tuple containing root certificate, server certificate, and private key to
            start a secure SSL-enabled server. The tuple is expected to have three bytes
            elements in the following order:

                * CA certificate.
                * server certificate.
                * server private key.

    Returns
    -------
        hist: flwr.server.history.History. Object containing metrics from training.

    Examples
    --------
    Starting an insecure server:

    # >>> start_server()

    # Starting a SSL-enabled server:

    # >>> start_server(
    # >>>     certificates=(
    # >>>         Path("/crts/root.pem").read_bytes(),
    # >>>         Path("/crts/localhost.crt").read_bytes(),
    # >>>         Path("/crts/localhost.key").read_bytes()
    # >>>     )
    # >>> )
    """
    initialized_server, initialized_config = _init_defaults(
        server=server,
        config=config,
        strategy=strategy,
        client_manager=client_manager,
    )

    # Start gRPC server
    grpc_server = start_grpc_server(
        client_manager=initialized_server.client_manager(),
        server_address=server_address,
        max_message_length=grpc_max_message_length,
        certificates=certificates,
    )
    num_rounds = initialized_config.num_rounds
    ssl_status = "enabled" if certificates is not None else "disabled"
    msg = f"Flower server running ({num_rounds} rounds), SSL is {ssl_status}"
    log(INFO, msg)

    hist = _fl(
        server=initialized_server,
        config=initialized_config,
        force_final_distributed_eval=force_final_distributed_eval,
    )

    # Stop the gRPC server
    grpc_server.stop(grace=1)

    return hist



def _init_defaults(
    server: Optional[Server],
    config: Optional[Dict[str, Union[int, Optional[float]]]],
    strategy: Optional[Strategy],
    client_manager: Optional[ClientManager],
) -> Tuple[Server, Config]:
    # Create server instance if none was given
    if server is None:
        if client_manager is None:
            client_manager = SimpleClientManager()
        if strategy is None:
            strategy = FedAvg()
        server = Server(client_manager=client_manager, strategy=strategy)

    # Set default config values
    if config is None:
        config = {}

    conf = Config(**config)  # type: ignore

    return server, conf


def _fl(
    server: Server,
    config: Config,
    force_final_distributed_eval: bool,
) -> History:
    # Fit model
    hist = server.fit(num_rounds=config.num_rounds, timeout=config.round_timeout)
    log(INFO, "app_fit: losses_distributed %s", str(hist.losses_distributed))
    log(INFO, "app_fit: metrics_distributed %s", str(hist.metrics_distributed))
    log(INFO, "app_fit: losses_centralized %s", str(hist.losses_centralized))
    log(INFO, "app_fit: metrics_centralized %s", str(hist.metrics_centralized))

    if force_final_distributed_eval:
        # Temporary workaround to force distributed evaluation
        server.strategy.eval_fn = None  # type: ignore

        # Evaluate the final trained model
        res = server.evaluate_round(rnd=-1, timeout=config.round_timeout)
        if res is not None:
            loss, _, (results, failures) = res
            log(INFO, "app_evaluate: federated loss: %s", str(loss))
            log(
                INFO,
                "app_evaluate: results %s",
                str([(res[0].cid, res[1]) for res in results]),
            )
            log(INFO, "app_evaluate: failures %s", str(failures))
        else:
            log(INFO, "app_evaluate: no evaluation result")

    # Graceful shutdown
    server.disconnect_all_clients(timeout=config.round_timeout)

    return hist

# Choose which nodes

# Define metric aggregation function
def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    # Multiply accuracy of each client by number of examples used
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    return {"accuracy": sum(accuracies) / sum(examples)}


# Get Weight
class SaveModelStrategy(fl.server.strategy.FedAvg):
    def aggregate_fit(
        self,
        rnd: int,
        results,
        failures,
    ) -> Optional[fl.common.Weights]:
        weights = super().aggregate_fit(rnd, results, failures)
        # weights = weighted_average
        if weights is not None:
            # Save weights
            print(f"Saving round {rnd} weights...")
            np.savez(f"round-{rnd}-weights.npz", *weights)
        return weights


# Define strategy
strategy = SaveModelStrategy(
    fraction_fit=1.0,
    min_fit_clients=2,
    min_available_clients=2,
    # eval_fn=get_eval_fn(testloader),
    # on_fit_config_fn=fit_config,
)

# Define strategy
# strategy = fl.server.strategy.FedAvg(evaluate_metrics_aggregation_fn=weighted_average)

# Start Flower server
fl.server.start_server(
    # server_address="localhost:8080",
    server_address = DEFAULT_SERVER_ADDRESS,
    config = {"num_rounds": 3},
    strategy = strategy,
    # certificates=(
    #     Path("/crts/root.pem").read_bytes(),
    #     Path("/crts/localhost.crt").read_bytes(),
    #     Path("/crts/localhost.key").read_bytes()
    # )
)