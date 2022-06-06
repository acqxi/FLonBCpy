# %%
import time
from typing import Any, Dict, List, Tuple, Union

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

%matplotlib inline


# %%
class ChainRecord():

    def __init__( self ) -> None:
        self.blockchain: List[ Dict[ str, Union[ str, int, List[ Any ] ] ] ] = [ {
            'pre': 0,
            'index': 0,
            'timestamp': 0,
            'nonce': 0,
            'model_hash': '',
            'previous_model_acc': 0
        } ]
        self.block_chain_pos: List[ int ] = []
        self.block_time_pos: List[ int ] = []
        self.chains_members: List[ List[ int ] ] = []
        self.chains_last_member: List[ int ] = []

    def re_calcu_all_block( self ):
        self.block_chain_pos: List[ int ] = [ 0 ]
        self.block_time_pos: List[ int ] = [ 0 ]
        self.chains_members: List[ List[ int ] ] = [ [ 0 ] ]
        self.chains_last_member: List[ int ] = [ 0 ]

        for idx, data in enumerate( self.blockchain ):
            if idx == 0:
                continue
            pre = data[ 'pre' ]
            print( f'work {idx} : {pre} -> {idx}', end='' )
            if pre not in self.chains_last_member:  # new branch
                self.block_chain_pos.append( len( self.chains_last_member ) )
                self.block_time_pos.append( self.block_time_pos[ pre ] + 1 )
                self.chains_last_member.append( idx )
                self.chains_members.append( [ idx ] )
            else:
                self.block_chain_pos.append( self.block_chain_pos[ pre ] )
                self.block_time_pos.append( self.block_time_pos[ pre ] + 1 )
                self.chains_members[ self.block_chain_pos[ idx ] ].append( idx )
                self.chains_last_member[ self.block_chain_pos[ idx ] ] = idx

            print(
                f', pos: ({self.block_chain_pos[ pre ]}, {self.block_time_pos[ pre ]})',
                f'-> ({self.block_chain_pos[ idx ]}, {self.block_time_pos[ idx ]})' )

    def show_chain( self, limit: int = -1, debug:bool=True ) -> None:
        ax = plt.gca()
        ax.set_xlabel( 'time' )
        ax.set_ylabel( 'chains' )
        ax.set_title( 'BlockChain' )
        grid_size = max( max( self.block_time_pos ), len( self.chains_members ) ) + 1
        ax.set_xlim( -1, grid_size )
        ax.set_ylim(
            int( -0.5 * grid_size + len( self.chains_members ) / 2 ), int( 0.5 * grid_size + len( self.chains_members ) / 2 ) )
        ax.xaxis.set_major_locator( plt.MaxNLocator( 1 ) )
        ax.yaxis.set_major_locator( plt.MaxNLocator( 1 ) )
        ax.grid( True )
        for i, data in enumerate( self.blockchain ):
            if limit >= 0 and i > limit:
                break
            color = list( mcolors.TABLEAU_COLORS.keys() )[ self.block_chain_pos[ i ] % len( mcolors.TABLEAU_COLORS ) ]
            y1, x1 = self.block_chain_pos[ data[ 'pre' ] ], self.block_time_pos[ data[ 'pre' ] ]
            y2, x2 = self.block_chain_pos[ i ], self.block_time_pos[ i ]
            if debug : print( f'draw: ({x1},{y1}) -> ({x2},{y2})' )
            plt.scatter( x2, y2, c=color )
            plt.plot( ( x1, x2 ), ( y1, y2 ), c=color )
        plt.show()

    def show_chain_animation( self , wait:float=1) -> None:
        if 'inline' in matplotlib.get_backend():
            from IPython import display
        for i in range( len( self.blockchain ) ):
            self.show_chain( i , debug=False)
            time.sleep(wait)
            display.clear_output(wait=True)


# %%
chain_record = ChainRecord()
tmp = [ 0, 0, 1, 2, 2, 3, 4, 6, 7, 8 ]
chain_record.blockchain = [ {
    'pre': p,
    'index': i,
    'timestamp': 0,
    'nonce': 0,
    'model_hash': '',
    'previous_model_acc': 0
} for i, p in enumerate( tmp ) ]
chain_record.re_calcu_all_block()
chain_record.show_chain()
# %%
chain_record.show_chain_animation()
# %%
