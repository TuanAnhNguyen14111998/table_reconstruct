import time
import cv2
import networkx
import numpy as np

def encode_coord(box):
    '''
    [xmin, ymin, xmax, ymax] --> 'xmin,ymin,xmax,ymax'
    '''
    return ",".join([str(coord) for coord in box])


class TableReconstructor():

    def __init__(self, cells):
        self.cells = cells
        self.vertex_dict = self.__make_vertex_dict(self.cells)
        self.graph = {}
        self.width_key = "width_table"
        self.heigh_key = 'height_table'


    def __make_vertex_dict(self, cells):
        vertex_dict = {}
        for idx, cell in enumerate(cells):
            vertex_dict[idx] = cell

        return vertex_dict


    def create_connections_by_axis(self, cells, axis='x'):
        connections_by_axis = {}
        for index_cell_i in range(len(cells)-1):
            for index_cell_j in range(index_cell_i+1, len(cells)):
                if self.check_overlap_by_axis(cells[index_cell_i], cells[index_cell_j], axis=axis) or self.check_overlap_by_axis(cells[index_cell_j], cells[index_cell_i], axis=axis):
                    if index_cell_i not in connections_by_axis:
                        connections_by_axis[index_cell_i] = [index_cell_j]
                    else:
                        connections_by_axis[index_cell_i].append(index_cell_j)

                    if index_cell_j not in connections_by_axis:
                        connections_by_axis[index_cell_j] = [index_cell_i]
                    else:
                        connections_by_axis[index_cell_j].append(index_cell_i)
                else:
                    continue

        return connections_by_axis


    def sort_func(self, clique, set_cells_not_for_compare,  axis='x'):
        '''
        return box that have x_center min 
        '''
        if axis == 'x':
            min_x = 10000
            for idx, node in enumerate(clique):
                if node not in set_cells_not_for_compare:
                    
                    node_x = self.cal_center_box(self.vertex_dict[node])[0]
                    if node_x < min_x:
                        min_x = node_x
            return min_x
        else:
            min_y = 10000
            for idx, node in enumerate(clique):
                if node not in set_cells_not_for_compare:
                    node_y = self.cal_center_box(self.vertex_dict[node])[1]
                    if node_y < min_y:
                        min_y = node_y
            return min_y


    def find_all_max_clique(self, connections):
        G = networkx.Graph()
        for node, neighbors in connections.items():
            for neighbor_node in neighbors:
                G.add_edge(node, neighbor_node)
        all_cliques = networkx.algorithms.clique.find_cliques(G)
        return [clique for clique in all_cliques]


    def get_cells_not_for_comparing(self, cliques):
        if len(cliques) == 0:
            return set()
        clique_max = max(cliques, key= lambda clique : len(clique))
        max_length_clique = len(clique_max)
        cliques_not_max_length = [clique for clique in cliques if len(clique) < max_length_clique]
        set_cells_not_for_compare = set([cell for clique in cliques_not_max_length for cell in clique])

        return set_cells_not_for_compare


    def process(self):
        t1 = time.time()
        if len(self.cells) == 1:
            x_cliques = [[0]]
            y_cliques = [[0]]
        else:
            x_connections = self.create_connections_by_axis(self.cells, axis='x')
            y_connections = self.create_connections_by_axis(self.cells, axis='y')

            x_cliques = self.find_all_max_clique(x_connections)
            y_cliques = self.find_all_max_clique(y_connections)
            # print("x_cliques", x_cliques)
            # print("y_cliques", y_cliques)
            x_cliques = [list(clique) for clique in x_cliques]
            y_cliques = [list(clique) for clique in y_cliques]

            x_cliques = [self.sort_clique_by_axis(clique, axis='x') for clique in x_cliques]
            y_cliques = [self.sort_clique_by_axis(clique, axis='y') for clique in y_cliques]

            # multi row, one columns
            if len(x_cliques) == 1 and len(x_cliques[0]) == len(self.cells) and len(y_cliques) == 0:  # one row, multi column
                y_cliques = []
                for idx in x_cliques[0]:
                    y_cliques.append([idx])

        set_x_cells_not_for_compare = self.get_cells_not_for_comparing(x_cliques)
        set_y_cells_not_for_compare = self.get_cells_not_for_comparing(y_cliques)
        
        x_cliques_sorted_to_row = sorted(x_cliques, key=lambda clique: self.sort_func(clique,set_y_cells_not_for_compare, axis='y', ))
        y_cliques_sorted_to_columns = sorted(y_cliques, key=lambda clique: self.sort_func(clique, set_x_cells_not_for_compare, axis='x'))

        # Create table with key: hash of coord of cell, value: index cell in table
        table = {}
        for vertex in range(len(self.cells)):
            hash_key = self.vertex2key(vertex)
            table[hash_key] = {'x': [], 'y': []}

        for x_index, clique in enumerate(x_cliques_sorted_to_row):
            for vertex in self.vertex_dict.keys():
                if vertex in clique:
                    hash_key = self.vertex2key(vertex)
                    table[hash_key]['x'].append(x_index)
                    
        for y_index, clique in enumerate(y_cliques_sorted_to_columns):
            for vertex in self.vertex_dict.keys():
                if vertex in clique:
                    hash_key = self.vertex2key(vertex)
                    table[hash_key]['y'].append(y_index)

        # Create table_doc:
        table_doc= self.convert_table_to_doc_format(table_dict=table, n_cols=len(y_cliques_sorted_to_columns)\
                                                    , n_rows=len(x_cliques_sorted_to_row))         
        return table_doc

#     def cal_size_box(self, box):
#         w = box[2]  - box[0]
#         h = box[3] - box[1]
#         return w, h

    def convert_table_to_doc_format(self, table_dict, n_cols, n_rows):
        """Convert table_dict to table for doc format

        Args:
            table_dict (dict): key: "xmin,ymin,xmax,ymax", value: {'x': [], 'y': []}
            n_cols (int): number of columns in table
            n_rows (int): number of rows in table

        Returns:
            table_doc (list): table[x][y] = key of table_dict/"merge_cell_____x,y"
        """
        table_doc = [['-1' for _ in range(n_cols)]  for _ in range(n_rows)]
        # Get ratio size of cell
        for key, value in table_dict.items():
            if key != self.width_key and key != self.heigh_key:
                x_coords, y_coords = value['x'], value['y']
               
                for idx, x in enumerate(x_coords):
                    for idy, y in enumerate(y_coords):
                        if idx == 0 and idy == 0:  
                            table_doc[x][y] = key
                            x_same, y_same = x, y
                        else:
                            table_doc[x][y] = "merge_cell_____"+ ",".join([str(x_same), str(y_same)])
        return table_doc


    def vertex2key(self, vertex):
        coord_vertex = self.vertex_dict[vertex]
        hash_key = encode_coord(coord_vertex)
        return hash_key


    def sort_clique_by_axis(self, clique, axis='x'):
        if axis == 'x':
            return sorted(clique, key=lambda vertext: self.vertex_dict[vertext][0])
        else:
            return sorted(clique, key=lambda vertext: self.vertex_dict[vertext][1])


    def check_overlap_by_axis(self, cell_1, cell_2, axis='x'):
        center_box_cell_1 = self.cal_center_box(cell_1)
        x_center_cell_1, y_center_cell_1 = center_box_cell_1
        x1, y1, x2, y2 = cell_2
        if axis == 'x':
            return y1 < y_center_cell_1 < y2
        else:
            return x1 < x_center_cell_1 < x2


    def cal_center_box(self, box):
        x_center = (box[0] + box[2]) // 2
        y_center = (box[1] + box[3]) // 2
        center_box = [x_center, y_center]

        return center_box
