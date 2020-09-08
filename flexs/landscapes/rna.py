import numpy as np
import RNA

import flexs


class RNAFolding(flexs.Landscape):
    def __init__(self, threshold=False, norm_value=1, reverse=False):
        super().__init__(name="RNAFolding")

        self.sequences = {}
        self.noise = noise
        self.threshold = threshold
        self.norm_value = norm_value
        self.reverse = reverse

    def _fitness_function(self, sequence):
        _, fe = RNA.fold(sequence)

        if self.threshold != False:
            if -fe > self.threshold:

                return int(not self.reverse)
            else:
                return int(self.reverse)

        return -fe / self.norm_value

    def get_fitness(self, sequence):
        if self.noise == 0:
            if sequence in self.sequences:
                return self.sequences[sequence]
            else:
                self.sequences[sequence] = self._fitness_function(sequence)
                return self.sequences[sequence]
        else:
            self.sequences[sequence] = self._fitness_function(
                sequence
            ) + np.random.normal(scale=self.noise)
        return self.sequences[sequence]


class RNABinding(flexs.Landscape):
    """An RNA binding landscape"""

    def __init__(
        self, targets, seq_length, threshold=False, conserved_region=None, name=None
    ):
        if name is None:
            name = f"RNABinding_T{targets}_L{seq_length}"
        super().__init__(name)

        self.targets = targets
        self.seq_length = seq_length
        self.threshold = threshold
        self.conserved_region = conserved_region
        self.norm_value = self.compute_maximum_binding_possible()

        self.sequences = {}

    def compute_maximum_binding_possible(self):
        map1 = {"A": "U", "C": "G", "G": "C", "U": "A"}

        total_energy = 0
        for target in self.targets:
            match = "".join(map1[x] for x in target)[::-1]
            total_energy += RNA.duplexfold(match, target).energy

        return -total_energy

    def _fitness_function(self, sequences):
        fitnesses = []

        total_target_lengths = sum(len(t) for t in self.targets)
        for seq in sequences:

            # Check that sequence is of correct length
            if len(seq) != self.seq_length:
                raise ValueError(
                    f"All sequences in `sequences` must be of length {self.seq_length}"
                )

            # If `self.conserved_region` is not None, check that the region is conserved
            if self.conserved_region is not None:
                start = self.conserved_region["start"]
                pattern = self.conserved_region["pattern"]

                # If region not conserved, fitness is 0
                if seq[start : start + len(pattern)] != pattern:
                    fitnesses.append(0)
                    continue

            # Energy is sum of binding energies across all targets
            energy = sum(RNA.duplexfold(target, seq).energy for target in self.targets)
            if self.threshold:
                fitness = int(-energy > self.threshold)
            else:
                fitness = -energy / (self.norm_value * len(seq) / total_target_lengths)

            fitnesses.append(fitness)

        return np.array(fitnesses)


def registry():
    """
    Returns a dictionary of problems of the form:
    `{
        "problem name": {
            "params": ...,
            "starts": ...
        },
        ...
    }`

    where `flexs.landscapes.RNABinding(**problem["params"])` instantiates the
    RNA binding landscape for the given set of parameters.

    Returns:
        dict: Problems in the registry.

    """

    # RNA target sequences
    targets = [
        "GAACGAGGCACAUUCCGGCUCGCCCGGCCCAUGUGAGCAUGGGCCGGACCCCGUCCGCGCGGGGCCCCCGCGCGGACGGGGGCGAGCCGGAAUGUGCCUC",
        "GAGGCACAUUCCGGCUCGCCCCCGUCCGCGCGGGGGCCCCGCGCGGACGGGGUCCGGCCCGCGCGGGGCCCCCGCGCGGGAGCCGGAAUGUGCCUCGUUC",
        "CCGGUGAUACUGUUAGUGGUCACGGUGCAUUUAUAGCGCUAAAGUACAGUCUUCCCCUGUUGAACGGCGCCAUUGCAUACAGGGCCAGCCGCGUAACGCC",
        "UAAGAGAGCGUAAAAAUAGAGAUAUGUUCUUGGGUCAGGGCUAUGCGUACCCCAUGAGAGUAAAUCAUACCCCCAAUGGGCUUCGGCGGAAAUUCACUUA",
    ]

    # Starting sequences of lengths 14, 50, and 100
    starts = {
        14: [
            "AUGGGCCGGACCCC",
            "GCCCCGCCGGAAUG",
            "UCUUGGGGACUUUU",
            "GGAUAACAAUUCAU",
            "CCCAUGCGCGAUCA",
        ],
        50: [
            "GAACGAGGCACAUUCCGGCUCGCCCGGCCCAUGUGAGCAUGGGCCGGACC",
            "CCGUCCGCGCGGGGCCCCCGCGCGGACGGGGGCGAGCCGGAAUGUGCCUC",
            "AUGUUUCUUUUAUUUAUCUGAGCAUGGGCGGGGCAUUUGCCCAUGCAAUU",
            "UAAACGAUGCUUUUGCGCCUGCAUGUGGGUUAGCCGAGUAUCAUGGCAAU",
            "AGGGAAGAUUAGAUUACUCUUAUAUGACGUAGGAGAGAGUGCGGUUAAGA",
        ],
        100: [
            "GAACGAGGCACAUUCCGGCUCGCCCGGCCCAUGUGAGCAUGGGCCGGACCCCGUCCGCGCGGGGCCCCCGCGCGGACGGGGGCGAGCCGGAAUGUGCCUC",
            "AGCAUCUCGCCGUGGGGGCGGGCCCGGCCCAUGUGAGCAUGCGUAGGUUUAUCCCAUAGAGGACCCCGGGAGAACUGUCCAAUUGGCUCCUAGCCCACGC",
            "GGCGGAUACUAGACCCUAUUGGCCCGGCCCAUGUGAGCAUGGCCCCAGAUCUUCCGCUCACUCGCAUAUUCCCUCCGGUUAAGUUGCCGUUUAUGAAGAU",
            "UUGCAGGUCCCUACACCUCCGGCCCGGCCCAUGUGACCAUGAAUAGUCCACAUAAAAACCGUGAUGGCCAGUGCAGUUGAUUCCGUGCUCUGUACCCUUU",
            "UGGCGAUGAGCCGAGCCGCCAUCGGACCAUGUGCAAUGUAGCCGUUCGUAGCCAUUAGGUGAUACCACAGAGUCUUAUGCGGUUUCACGUUGAGAUUGCA",
        ],
    }

    problems = {}

    # Single target problems - 4 of these
    for t in range(len(targets)):
        for length, start in starts.items():
            name = f"L{length}_RNA{t+1}"
            problems[name] = {
                "params": {"targets": [targets[t]], "seq_length": length,},
                "starts": start,
            }

    # Two-target problems
    for t1 in range(len(targets)):
        for t2 in range(t1 + 1, len(targets)):
            for length, targets in starts.items():
                name = f"L{length}_RNA{t1+1}+{t2+1}"
                problems[name] = {
                    "params": {
                        "targets": [targets[t1], targets[t2]],
                        "seq_length": length,
                    },
                    "starts": start,
                }

    # Two-target problems with conserved portion
    for t1 in range(len(targets)):
        for t2 in range(t1 + 1, len(targets)):
            name = f"C21_L100_RNA{t1+1}+{t2+1}"
            problems[name] = {
                "params": {
                    "targets": [targets[t1], targets[t2]],
                    "seq_length": 100,
                    "conserved_region": {
                        "start": 21,
                        "pattern": "GCCCGGCCCAUGUGAGCAUG",
                    },
                },
                "starts": starts[100],
            }

    return problems
