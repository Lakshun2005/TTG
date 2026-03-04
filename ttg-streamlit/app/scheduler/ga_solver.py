"""
Genetic Algorithm Solver for Timetable Scheduling.

Uses evolutionary optimization to find valid, conflict-free timetables.
Hard constraints (fitness = -inf): No double-booking of faculty, section, or room.
Soft constraints (bonus): Faculty expertise match, workload spread.
"""

import random
import numpy as np
from typing import Dict, List, Optional, Tuple
from app.scheduler.domain_builder import Variable
from app.logger import get_logger

logger = get_logger(__name__)

Assignment = Dict[str, Tuple[int, int]]


class GeneticAlgorithmSolver:
    """
    Genetic Algorithm for timetable scheduling.

    Chromosome: list of (timeslot_id, room_id) tuples, one per variable.
    """

    def __init__(
        self,
        variables: List[Variable],
        domains: Dict[str, List[Tuple[int, int]]],
        population_size: int = 100,
        generations: int = 500,
        mutation_rate: float = 0.15,
        elite_ratio: float = 0.1,
        tournament_size: int = 5,
    ):
        self.variables = variables
        self.domains = domains
        self.var_keys = [v.key() for v in variables]
        self.var_map = {v.key(): v for v in variables}
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite_count = max(2, int(population_size * elite_ratio))
        self.tournament_size = tournament_size

    # ── Chromosome helpers ───────────────────────────────────────────────

    def _random_chromosome(self) -> List[Tuple[int, int]]:
        """Generate a random chromosome (one gene per variable)."""
        chrom = []
        for key in self.var_keys:
            domain = self.domains[key]
            if domain:
                chrom.append(random.choice(domain))
            else:
                chrom.append((-1, -1))  # invalid sentinel
        return chrom

    def _decode(self, chromosome: List[Tuple[int, int]]) -> Assignment:
        """Convert chromosome to an Assignment dict."""
        return {key: gene for key, gene in zip(self.var_keys, chromosome)}

    # ── Fitness ───────────────────────────────────────────────────────────

    def _fitness(self, chromosome: List[Tuple[int, int]]) -> float:
        """
        Evaluate a chromosome. Higher = better.
        Returns large negative value for hard constraint violations.
        """
        score = 0.0
        n = len(self.var_keys)

        # Build lookup: timeslot -> list of (var_key_index, room_id)
        ts_assignments: Dict[int, List[Tuple[int, int]]] = {}
        for i in range(n):
            ts_id, room_id = chromosome[i]
            if ts_id == -1:
                score -= 10000  # invalid domain
                continue
            ts_assignments.setdefault(ts_id, []).append((i, room_id))

        # Check hard constraints for each timeslot
        for ts_id, entries in ts_assignments.items():
            seen_faculty = set()
            seen_section = set()
            seen_room = set()

            for idx, room_id in entries:
                var = self.var_map[self.var_keys[idx]]

                # Faculty double-booking
                if var.faculty_id in seen_faculty:
                    score -= 1000
                seen_faculty.add(var.faculty_id)

                # Section double-booking
                if var.section_id in seen_section:
                    score -= 1000
                seen_section.add(var.section_id)

                # Room double-booking
                if room_id in seen_room:
                    score -= 1000
                seen_room.add(room_id)

        # Soft constraint: reward diversity of timeslots used per section
        section_timeslots: Dict[int, set] = {}
        for i in range(n):
            var = self.var_map[self.var_keys[i]]
            ts_id = chromosome[i][0]
            section_timeslots.setdefault(var.section_id, set()).add(ts_id)

        for sid, ts_set in section_timeslots.items():
            score += len(ts_set) * 10  # reward spread

        return score

    # ── Selection ─────────────────────────────────────────────────────────

    def _tournament_select(
        self, population: List[List[Tuple[int, int]]], fitnesses: List[float]
    ) -> List[Tuple[int, int]]:
        """Tournament selection: pick best from random subset."""
        indices = random.sample(range(len(population)), min(self.tournament_size, len(population)))
        best = max(indices, key=lambda i: fitnesses[i])
        return list(population[best])

    # ── Crossover ─────────────────────────────────────────────────────────

    def _crossover(
        self, parent1: List[Tuple[int, int]], parent2: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """Uniform crossover."""
        child = []
        for g1, g2 in zip(parent1, parent2):
            child.append(g1 if random.random() < 0.5 else g2)
        return child

    # ── Mutation ──────────────────────────────────────────────────────────

    def _mutate(self, chromosome: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Randomly replace genes with valid domain values."""
        for i in range(len(chromosome)):
            if random.random() < self.mutation_rate:
                domain = self.domains[self.var_keys[i]]
                if domain:
                    chromosome[i] = random.choice(domain)
        return chromosome

    # ── Main solve loop ──────────────────────────────────────────────────

    def solve(self) -> Optional[Assignment]:
        """Run the GA and return the best valid assignment, or None."""
        logger.info(
            f"GA starting: {len(self.variables)} variables, "
            f"pop={self.population_size}, gens={self.generations}"
        )

        # Initialize population
        population = [self._random_chromosome() for _ in range(self.population_size)]

        best_ever = None
        best_fitness_ever = float("-inf")

        for gen in range(self.generations):
            # Evaluate fitness
            fitnesses = [self._fitness(c) for c in population]

            # Track best
            gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
            gen_best_fitness = fitnesses[gen_best_idx]

            if gen_best_fitness > best_fitness_ever:
                best_fitness_ever = gen_best_fitness
                best_ever = list(population[gen_best_idx])

            # Early termination if perfect solution found (no violations)
            if gen_best_fitness >= 0:
                logger.info(f"GA found valid solution at generation {gen} (fitness={gen_best_fitness})")
                return self._decode(population[gen_best_idx])

            if gen % 50 == 0:
                logger.debug(f"GA gen {gen}: best_fitness={gen_best_fitness:.0f}")

            # Elitism: keep top N
            elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)[
                : self.elite_count
            ]
            new_population = [list(population[i]) for i in elite_indices]

            # Fill rest with crossover + mutation
            while len(new_population) < self.population_size:
                parent1 = self._tournament_select(population, fitnesses)
                parent2 = self._tournament_select(population, fitnesses)
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                new_population.append(child)

            population = new_population

        # Check if best-ever is valid
        if best_ever is not None and self._fitness(best_ever) >= 0:
            logger.info(f"GA returning best-ever solution (fitness={best_fitness_ever})")
            return self._decode(best_ever)

        logger.warning(f"GA failed to find valid solution after {self.generations} generations")
        return None
