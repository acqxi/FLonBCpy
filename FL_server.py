from typing import List, Tuple, Optional
import numpy as np

import flwr as fl
from flwr.common import Metrics

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
        # weights = super().aggregate_fit(rnd, results, failures)
        weights = weighted_average
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
    server_address = 'localhost:' + input("Enter server PORT:"),
    config = {"num_rounds": 3},
    strategy = strategy,
)
