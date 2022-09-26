import rdflib
import os
import json
from rdflib.namespace import RDF, XSD
import re

BDB_NS = "bdb://"


def has_type(type, asset):
    """
    This function takes a semantic type @type and an asset @asset
    and answers whether the rdf of @asset contains any subject
    carrying @type.

    Example:
    For a valid order asset @order_asset
    >>>> Semantics.has_type(Semantics().SCVL.Order, order_asset)
    True
    """

    # Check that the asset is stripped down to its data
    if 'data' in asset.keys():
        asset = asset['data']
    return Semantics().triple_exists(asset['rdf'], (None, Semantics.RDF.type, type))

class Semantics:
    NODE_ID = "{}[id]/".format(BDB_NS)
    placeholder_pattern = r"{}\[id\]".format(BDB_NS)
    URI_pattern = r"(http:\/\/|bdb:\/\/).+#(?P<name>.+)"
    scvl_namespace = os.getenv('SCVL_ONTOLOGY', 'http://ontology.tno.nl/scvl#')
    SCVL = rdflib.Namespace(scvl_namespace)
    # Make RDF namespace part of Semantics class
    RDF = RDF

    context = {
        "scvl": scvl_namespace,
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
    }
    # Construct NamespaceManager
    nsMgr = rdflib.namespace.NamespaceManager(rdflib.Graph())
    for prefix, ns in context.items():
        nsMgr.bind(prefix, rdflib.URIRef(ns))

    '''
    Utility functions
    '''
    @classmethod
    def load_rdf(cls, serialized_data, data_format='json-ld'):
        g = rdflib.ConjunctiveGraph()

        try:
            g.parse(data=serialized_data, format=data_format)
        except:
            return False

        return g

    @classmethod
    def triple_exists(cls, data, triple=(None, None, None)):
        g = cls.load_rdf(json.dumps(data))

        def castValue(val):
            """
            Cast the values of the triple in terms
            that rdflib understands, using `from_n3`.
            Crucially, from_n3 only builds literals
            if the values are in "" quotes, so arguments
            should be formatted before calling `triple_exists`.

            From_n3 also doesn't handle terms that are already nodes,
            so those must not be passed through from_n3 again.
            """
            if isinstance(val, rdflib.term.Node):
                return val
            else:
                return rdflib.util.from_n3(val, nsm=cls.nsMgr)

        triple = tuple(map(castValue, triple))
        # print("Searching for triple: {}".format(triple))

        for s, p, o in g.triples(triple):
            return True
        return False

    @classmethod
    def get_nodes(cls, data):
        g = cls.load_rdf(json.dumps(data))

        nodes = []
        for n in g.all_nodes():
            if isinstance(n, rdflib.term.URIRef):
                if re.match(cls.placeholder_pattern, n):
                    for s, p, o in g.triples((n, RDF.type, None)):
                        nodes.append((s, o))
        return nodes
        