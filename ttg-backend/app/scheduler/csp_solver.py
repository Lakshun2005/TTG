from typing import Dict, List, Optional, Tuple
from collections import deque
from app.scheduler.domain_builder import Variable
from app.scheduler.constraints import is_consistent, Assignment


class CSPSolver:
    def __init__(self, variables: List[Variable], domains: Dict[str, List[Tuple[int, int]]]):
        self.variables = variables
        self.domains = {v.key(): list(domains[v.key()]) for v in variables}
        self.var_map: Dict[str, Variable] = {v.key(): v for v in variables}
        self.neighbors: Dict[str, List[str]] = self._build_neighbors()

    def _build_neighbors(self) -> Dict[str, List[str]]:
        neighbors: Dict[str, List[str]] = {v.key(): [] for v in self.variables}
        for i, v1 in enumerate(self.variables):
            for j, v2 in enumerate(self.variables):
                if i >= j:
                    continue
                # Neighbors share faculty, section, or could conflict on rooms
                if (v1.faculty_id == v2.faculty_id or
                        v1.section_id == v2.section_id):
                    neighbors[v1.key()].append(v2.key())
                    neighbors[v2.key()].append(v1.key())
        return neighbors

    def ac3(self) -> bool:
        """AC-3 constraint propagation to reduce domains before search."""
        queue = deque()
        for v_key in self.var_map:
            for neighbor_key in self.neighbors[v_key]:
                queue.append((v_key, neighbor_key))

        while queue:
            xi_key, xj_key = queue.popleft()
            if self._revise(xi_key, xj_key):
                if not self.domains[xi_key]:
                    return False
                for xk_key in self.neighbors[xi_key]:
                    if xk_key != xj_key:
                        queue.append((xk_key, xi_key))
        return True

    def _revise(self, xi_key: str, xj_key: str) -> bool:
        """Remove values from xi's domain that have no consistent support in xj."""
        revised = False
        xi = self.var_map[xi_key]
        xj = self.var_map[xj_key]

        to_remove = []
        for val_i in self.domains[xi_key]:
            ts_i, room_i = val_i
            has_support = False
            for val_j in self.domains[xj_key]:
                ts_j, room_j = val_j
                conflict = False
                if ts_i == ts_j:
                    if xi.faculty_id == xj.faculty_id:
                        conflict = True
                    elif xi.section_id == xj.section_id:
                        conflict = True
                    elif room_i == room_j:
                        conflict = True
                if not conflict:
                    has_support = True
                    break
            if not has_support:
                to_remove.append(val_i)
                revised = True

        for val in to_remove:
            self.domains[xi_key].remove(val)

        return revised

    def _select_unassigned_variable(self, assignment: Assignment) -> Optional[str]:
        """MRV heuristic: pick unassigned variable with smallest domain."""
        unassigned = [v.key() for v in self.variables if v.key() not in assignment]
        if not unassigned:
            return None
        return min(unassigned, key=lambda k: len(self.domains[k]))

    def _order_domain_values(self, var_key: str, assignment: Assignment) -> List[Tuple[int, int]]:
        """LCV heuristic: prefer values that constrain neighbors least."""
        def count_eliminations(value: Tuple[int, int]) -> int:
            count = 0
            ts, room = value
            var = self.var_map[var_key]
            for neighbor_key in self.neighbors[var_key]:
                if neighbor_key in assignment:
                    continue
                neighbor_var = self.var_map[neighbor_key]
                for n_val in self.domains[neighbor_key]:
                    n_ts, n_room = n_val
                    if n_ts == ts:
                        if var.faculty_id == neighbor_var.faculty_id:
                            count += 1
                        elif var.section_id == neighbor_var.section_id:
                            count += 1
                        elif room == n_room:
                            count += 1
            return count

        return sorted(self.domains[var_key], key=count_eliminations)

    def _forward_check(
        self, var_key: str, value: Tuple[int, int], assignment: Assignment
    ) -> Optional[Dict[str, List[Tuple[int, int]]]]:
        """Prune domains of unassigned neighbors after assigning var=value."""
        ts, room = value
        var = self.var_map[var_key]
        pruned: Dict[str, List[Tuple[int, int]]] = {}

        for neighbor_key in self.neighbors[var_key]:
            if neighbor_key in assignment:
                continue
            neighbor_var = self.var_map[neighbor_key]
            to_remove = []
            for n_val in self.domains[neighbor_key]:
                n_ts, n_room = n_val
                if n_ts == ts:
                    conflict = False
                    if var.faculty_id == neighbor_var.faculty_id:
                        conflict = True
                    elif var.section_id == neighbor_var.section_id:
                        conflict = True
                    elif room == n_room:
                        conflict = True
                    if conflict:
                        to_remove.append(n_val)

            if to_remove:
                if neighbor_key not in pruned:
                    pruned[neighbor_key] = []
                pruned[neighbor_key].extend(to_remove)
                for val in to_remove:
                    self.domains[neighbor_key].remove(val)
                if not self.domains[neighbor_key]:
                    # Restore all pruned values before returning failure
                    for k, vals in pruned.items():
                        self.domains[k].extend(vals)
                    return None

        return pruned

    def solve(self) -> Optional[Assignment]:
        """Run AC-3 preprocessing then backtracking search."""
        if not self.ac3():
            return None
        return self._backtrack({})

    def _backtrack(self, assignment: Assignment) -> Optional[Assignment]:
        if len(assignment) == len(self.variables):
            return assignment

        var_key = self._select_unassigned_variable(assignment)
        if var_key is None:
            return assignment

        for value in self._order_domain_values(var_key, assignment):
            var = self.var_map[var_key]
            if is_consistent(var, value, assignment, self.var_map):
                assignment[var_key] = value
                pruned = self._forward_check(var_key, value, assignment)

                if pruned is not None:
                    result = self._backtrack(assignment)
                    if result is not None:
                        return result
                    # Restore pruned domains on backtrack
                    for k, vals in pruned.items():
                        self.domains[k].extend(vals)

                del assignment[var_key]

        return None
