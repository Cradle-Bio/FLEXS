import abc

import flexs
from flexs.landscape import SEQUENCES_TYPE
from typing import Any, List, Union
import numpy as np

class Model(flexs.Landscape, abc.ABC):
    """Base structure for all models."""

    @abc.abstractmethod
    def train(self, sequences: SEQUENCES_TYPE, labels: List[Any]):
        """Train model.

        This function is called whenever you would want your model to update itself based on the set of sequences it has measurements for."""
        pass
