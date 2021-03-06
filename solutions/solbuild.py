# -*- coding: utf-8 -*-
'''
Created on 15.02.2013
@author: natalia
'''
from common import util
from solutions import calc

def build_solutions_tree(calc_relations, sought_variable, known_variables):

    soltree = SolutionsTree()
    fst_subtree, fst_paths = init_subtree_paths(
        calc_relations, sought_variable)

    if (fst_subtree.length() > 0):

        branches = get_branches(calc_relations, known_variables, fst_subtree, fst_paths)
        subtrees, to_del = get_subtrees_deadends(calc_relations, branches, fst_subtree)

        if (len(to_del) > 0):
            fst_subtree.filter_branches(to_del)

        soltree.update(fst_subtree)
        for subtree in subtrees:
            soltree.update(subtree)

    return soltree.get_data()


def init_subtree_paths(calc_relations, sought_variable):
    branches, fst_paths = [], []

    for calc_rel in calc_relations:
        if calc_rel.right_part == sought_variable:
            branches.append([calc_rel.get_id()])
            fst_paths.append(
                calc.Path(calc_rel.left_part, [sought_variable], [calc_relations.index(calc_rel)]))

    fst_subtree = SubTree(0, branches)   
    return fst_subtree, fst_paths

def get_branches(calc_relations, known_variables, fst_subtree, fst_paths):
    def update_paths_branches(calc_relations, curr_path, branches, known_variables):
        new_paths = []
        ignoreset = set(curr_path.ignorelist)
        changed = False                  

        for notation in curr_path.new_notation:
            for calc_rel in calc_relations:
                if (not(calc_rel.right_part in curr_path.ignorelist) and not(set(calc_rel.left_part).issubset(ignoreset))
                    and calc_rel.right_part == notation):
                    new_paths.append(
                        calc.Path(
                            calc_rel.left_part, curr_path.ignorelist +
                            curr_path.new_notation,
                            curr_path.indexes + [calc_relations.index(calc_rel)], curr_path.id))
                    branches.append(
                        (curr_path.id, curr_path.indexes[len(curr_path.indexes) - 1], calc_rel.get_id()))
                    changed = True

        if changed == False:
            #больше не можем продвинуться вперед, а нужных переменных не достигли. тогда это тупик, надо
            #удалить соответствующие ветки
            if (len(set(curr_path.new_notation).difference(set(known_variables))) > 0):
                branches = filter(lambda x: x[0] != curr_path.id, branches)

        return new_paths, branches

    curr_paths = fst_paths
    branches = []
    
    while(len(curr_paths) > 0):
        new_paths = []
        for path in curr_paths:
            paths, branches = update_paths_branches(
                calc_relations, path, branches, known_variables)
            new_paths = new_paths + paths
        curr_paths = new_paths

    # remove paths ids from each branch
    branches = map(lambda x: x[1:], branches)

    return branches


def get_subtrees_deadends(calc_relations, branches, fst_subtree):
    curr_nodes = fst_subtree.get_branches()
    sdc = SubtreesDeadendsConstructor()
    to_del = []
    is_fst_tree = True

    while (len(curr_nodes) > 0):
        for node_group in curr_nodes:
            if (type(node_group) is list):
                for node in node_group:
                    sdc.update(calc_relations, branches, node)
            else:
                sdc.update(calc_relations, branches, node_group)
        if is_fst_tree:
            to_del = sdc.get_deadends()
            is_fst_tree = False
        curr_nodes = sdc.get_new_curr_nodes()
        sdc.clear_new_curr_nodes()

    return sdc.get_subtrees(), to_del


class SubtreesDeadendsConstructor(object):

    def __init__(self):
        self.subtrees = []
        self.deadends = []
        self.new_curr_nodes = []

    def get_deadends(self):
        return self.deadends

    def get_new_curr_nodes(self):
        return self.new_curr_nodes

    def clear_new_curr_nodes(self):
        self.new_curr_nodes = []

    def get_subtrees(self):
        return self.subtrees

    def update(self, calc_relations, branches, node):
        node_given = set(
            util.get_calc_relation_by_id(calc_relations, node).left_part)
        filtered_branches = filter(lambda x: x[0] == node, branches)
        subtrees, to_del, new_curr_nodes = [], [], []
        if (len(filtered_branches) > 0):
            ids, new_branches = [], []
            calc_ids = map(lambda x: x[1], filtered_branches)
            for calc_id in calc_ids:
                calc_sought = set(
                    [util.get_calc_relation_by_id(calc_relations, calc_id).right_part])
                if (len(set.intersection(node_given, calc_sought)) == len(node_given)):
                    ids.append([calc_id])
                else:
                    new_branches.append(calc_id)
                new_curr_nodes.append(calc_id)
            if (len(new_branches) > 0):
                # TODO: write extra code for cases when length of calc_rel.left_part > 2
                ids = [new_branches]
            subtree = SubTree(node, ids)
            subtrees.append(subtree)
        else:
            to_del.append(node)

        self.subtrees = self.subtrees + subtrees
        self.deadends = self.deadends + to_del
        self.new_curr_nodes = self.new_curr_nodes + new_curr_nodes


class SolutionsTree(object):

    def __init__(self):
        self.data = {}

    def update(self, subtree):
        self.data[subtree.get_head()] = subtree.get_branches()

    def length(self):
        return len(self.data)

    def get_data(self):
        return self.data


class SubTree(object):

    def __init__(self, head=-1, branches=[]):
        self.head = head
        self.branches = branches

    def set_head(self, calc_id):
        self.head = calc_id

    def get_head(self):
        return self.head

    def get_branches(self):
        return self.branches

    def set_branches(self, branches):
        self.branches = branches

    def filter_branches(self, to_del):
        self.branches = filter(lambda x: not(x[0] in to_del), self.branches)

    def length(self):
        return len(self.branches)
