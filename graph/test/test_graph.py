"""Test functions for the graph library."""
import unittest
import graph

class GraphTestCase(unittest.TestCase):
    def testAddNode(self):
        # add_node
        g = graph.Graph()
        nnodes = 5
        nds = [g.add_node() for i in range(nnodes)]
        assert len(g.nodes)==nnodes, "Wrong number of nodes, expected: %d, got :%d" % (nnodes, len(g.nodes))
        # add nodes
        g = graph.Graph()
        nds = g.add_nodes(5)
        assert len(g.nodes)==nnodes, "Wrong number of nodes, expected: %d, got :%d" % (nnodes, len(g.nodes))
        g = graph.Graph()
        nds = g.add_nodes([None]*nnodes)
        assert len(g.nodes)==nnodes, "Wrong number of nodes, expected: %d, got :%d" % (nnodes, len(g.nodes))

    def testAddEdge(self):
        g = graph.Graph()
        nnodes = 5
        nds = [g.add_node() for i in range(nnodes)]
        eds = [g.add_edge(nds[i], nds[i+1]) for i in range(nnodes-1)]
        assert len(g.edges)==nnodes-1, "Wrong number of edges, expected: %d, got :%d" % (nnodes-1, len(g.edges))
        # the last nnodes-1 nodes should have in_degree==1,
        # and the first nnodes-1 out_degree==1
        for i in range(nnodes):
            if i>0: assert nds[i].in_degree()==1, "Wrong in_degree, expected: 1, got: %d." % nds[i].in_degree()
            if i<nnodes-1: assert nds[i].out_degree()==1, "Wrong out_degree, expected: 1, got: %d." % nds[i].out_degree()

    def testGetEdge(self):
        g = graph.Graph()
        nds = g.add_nodes(4)
        ed1 = g.add_edge(nds[0],nds[2])
        ed2 = g.add_edge(nds[1],nds[2])
        ed3 = g.add_edge(nds[2],nds[3])
        assert nds[2].get_edges_in().sort()==[ed1, ed2].sort()
        assert nds[2].get_edges().sort()==[ed1, ed2, ed3].sort()
        assert nds[2].get_edges_in(from_=nds[1])==[ed2]
        assert nds[2].get_edges_out(to_=nds[3])==[ed3]
        ed4 = g.add_edge(nds[3],nds[2])
        assert nds[2].get_edges(neighbor=nds[3]).sort()==[ed3,ed4].sort()

    def testRemoveEdge(self):
        g = graph.Graph()
        n0 = g.add_node()
        n1 = g.add_node()
        ed = g.add_edge(n0, n1)
        g.remove_edge(ed)
        assert len(g.edges)==0, "Wrong number of edges, expected: 0, got :%d" % len(g.edges)
        assert n0.out_degree()==0, "Wrong out_degree, expected: 0, got: %d." % n0.out_degree()
        assert n1.in_degree()==0, "Wrong in_degree, expected: 0, got: %d." % n1.in_degree()

    def testGetNeighbors(self):
        g = graph.Graph()
        nodes = g.add_tree( (1,2,(2,3)) )
        g.add_edge(nodes[1],nodes[2][1])
        outnodes = nodes[0].out_neighbors()
        assert nodes[1] in outnodes and nodes[2][0] in outnodes
        innodes = nodes[2][1].in_neighbors()
        assert nodes[2][0] in innodes and nodes[2][0] in innodes
        inoutnodes = nodes[1].neighbors()
        assert nodes[0] in inoutnodes and nodes[2][1] in inoutnodes

    def testAddTree(self):
        g = graph.Graph()
        a = None
        nodes = g.add_tree( (a, a, (a, a, a)) )
        assert len(g.nodes)==5
        assert len(g.edges)==4
        out_deg = graph.recursive_map(lambda x: x.out_degree(), nodes)
        assert out_deg==[2,0,[2,0,0]]
        in_deg = graph.recursive_map(lambda x: x.in_degree(), nodes)
        assert in_deg==[0,1,[1,1,1]]

    def testAddFullConnectivity(self):
        g = graph.Graph()
        layer0 = g.add_nodes(10)
        layer1 = g.add_nodes(5)
        g.add_full_connectivity(layer0, layer1)
        assert len(g.edges)==5*10
        assert map(lambda x: x.out_degree(), layer0)==[5]*10
        assert map(lambda x: x.in_degree(), layer1)==[10]*5
        
    def testTopologicalSort(self):
        g = graph.Graph()
        # the values correspond to the number of in-edges
        nds = g.add_tree( (0, 3, 1, 2) )
        g.add_edge(nds[2], nds[1])
        g.add_edge(nds[2], nds[3])
        g.add_edge(nds[3], nds[1])
        data = map(lambda x: x.data, g.topological_sort())
        assert data==[0,1,2,3]
        # make graph cyclic
        g.add_edge(nds[1], nds[0])
        self.assertRaises(graph.GraphTopologicalException, g.topological_sort)

    def testDFS(self):
        g = graph.Graph()
        nodes = g.add_tree( (1,(2,3),(2,3)) )
        data = map(lambda x: x.data, g.dfs(nodes[0]))
        assert data==[1,2,3,2,3]
        # test undirected version
        data = map(lambda x: x.data, g.undirected_dfs(nodes[2][1]))
        assert data==[3,2,1,2,3]
        # test node with two ingoing edges
        g = graph.Graph()
        nodes = g.add_tree( (1,2,(2,3)) )
        g.add_edge(nodes[1],nodes[2][1])
        data = map(lambda x: x.data, g.dfs(nodes[0]))
        assert data==[1,2,3,2]

    def testBFS(self):
        g = graph.Graph()
        nodes = g.add_tree( (1,(2,3),(2,3)) )
        data = map(lambda x: x.data, g.bfs(nodes[0]))
        assert data==[1,2,2,3,3]
        # test undirected version
        data = map(lambda x: x.data, g.undirected_bfs(nodes[2][1]))
        assert data==[3,2,1,2,3]
        # test node with two ingoing edges
        g = graph.Graph()
        nodes = g.add_tree( (1,2,(2,3)) )
        g.add_edge(nodes[1],nodes[2][1])
        data = map(lambda x: x.data, g.bfs(nodes[0]))
        assert data==[1,2,2,3]

    def testConnectedComponents(self):
        g = graph.Graph()
        nds0 = g.add_tree( (1, 1, 1) )
        nds1 = g.add_tree( (2, 2, 2) )
        comps = g.connected_components()
        comps = graph.recursive_map(lambda x: x.data, comps)
        assert len(comps)==2
        assert comps[0]==[1,1,1]
        assert comps[1]==[2,2,2]
        assert not g.is_weakly_connected()
        # connect graph
        g.add_edge(nds0[0], nds1[0])
        assert g.is_weakly_connected()        

def get_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GraphTestCase))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(get_suite())