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

    '''
    Project-specific semantics
    '''
    # TODO turn into classmethods
    #########
    # Orders
    #########

    # Helper for create_order
    def create_cargo(self, cargo_input, g, returns="graph"):
        
        cargo = rdflib.BNode()
        g.add((cargo, RDF.type, self.SCVL.Cargo))
        g.add((cargo, self.SCVL.typeOfCargo, rdflib.Literal(cargo_input['cargo_type'])))
        g.add((cargo, self.SCVL.typeOfPackages, rdflib.Literal(cargo_input['package_type'])))
        g.add((cargo, self.SCVL.numberOfPackages, rdflib.Literal(cargo_input['package_count'], datatype=rdflib.XSD.positiveInteger)))

        return cargo

    # Main order object creation method
    def create_order(self, order_input, g=None, returns="graph"):
        # Check if there is a graph object to build on
        if not g:
            g = rdflib.Graph()
        
        # Build 'root' order node
        order = rdflib.URIRef(self.NODE_ID)
        g.add((order, RDF.type, self.SCVL.Order))
        
        # Add cargo
        cargo = self.create_cargo(order_input['cargo'], g)
        g.add((order, self.SCVL.hasCargo, cargo))

        # Add other fields
        g.add((order, self.SCVL.placeOfAcceptance, rdflib.Literal(order_input['place_of_acceptance'])))
        g.add((order, self.SCVL.timeOfAcceptance, rdflib.Literal(order_input['time_of_acceptance'], datatype=XSD.dateTime)))
        g.add((order, self.SCVL.placeOfDelivery, rdflib.Literal(order_input['place_of_delivery'])))
        g.add((order, self.SCVL.timeOfDelivery, rdflib.Literal(order_input['time_of_delivery'], datatype=XSD.dateTime)))
        g.add((order, self.SCVL.referenceID, rdflib.Literal(order_input['reference_id']))),

        # Process output format
        if returns in ('dict', 'string'):
            rdf_str = g.serialize(format='json-ld', context=self.context)
            if returns == "dict":
                return json.loads(rdf_str)
            elif returns == "string":
                return rdf_str
        else:
            return g

    ##########
    # Events
    ##########

    def create_event(self, event_input, g=None, returns="graph"):
        # Check if there is a graph object to build on
        if not g:
            g = rdflib.Graph()

        # Build 'root' event node
        event = rdflib.URIRef(self.NODE_ID)
        g.add((event, RDF.type, self.SCVL.Event))

        # Add other fields
        g.add((event, self.SCVL.orderAssetID, rdflib.Literal(event_input['order_asset_id'])))
        # Extract event object from input
        event_object = event_input['event']
        g.add((event, self.SCVL.time, rdflib.Literal(event_object['time'])))
        g.add((event, self.SCVL.place, rdflib.Literal(event_object['place'])))
        g.add((event, self.SCVL.milestone, rdflib.Literal(event_object['milestone'])))
        
        # Process output format
        # TODO write an abstract 'create_semantics' func
        # to prevent duplication between this function and
        # creating orders.
        if returns in ('dict', 'string'):
            rdf_str = g.serialize(format='json-ld', context=self.context)
            # Serialize returns bytestring, decode before letting JSON handle it
            if isinstance(rdf_str, bytes):
                rdf_str = rdf_str.decode()
            if returns == "dict":
                return json.loads(rdf_str)
            elif returns == "string":
                return rdf_str
        else:
            return g

    '''
    Serialization
    '''
    def serialize_publications_asset(self, data):
        g = self.load_rdf(json.dumps(data))

        json_struct = []
        for s, p, o in g.triples((None, RDF.type, self.SCVL.Publication)):
            pub = self.serialize_semantic_asset(g, s)
            json_struct.append(pub)

        return json_struct

    def serialize_semantic_asset(self, g, subject):
        asset_object = {}
        for s, p, o in g.triples((subject, None, None)):
            property_name = re.match(self.URI_pattern, str(p)).group('name')
            if type(o) is rdflib.term.Literal or type(o) is rdflib.term.URIRef:
                asset_object[property_name] = str(o)
            elif type(o) is rdflib.term.BNode:
                asset_object[property_name] = self.serialize_semantic_asset(g, o)

        return asset_object