""" rdfmarshaller interfaces """

from eea.rdfmarshaller.interfaces import IField2Surf


class IDXField2Surf(IField2Surf):
    """ Extract values from Fields, to store them in the surf session """
