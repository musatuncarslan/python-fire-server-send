from connection import Connection
from saveData import SaveData
import socket
import logging
import h5py
import numpy as np

class Client:
    """
    Something something docstring.
    """

    def __init__(self, address, port, senddatafile):
        logging.info("Starting client and sending data to %s:%d", address, port)
        try:
            logging.debug("Opening folder...")
            self.hf = h5py.File(senddatafile,
                           "r")
        except Exception as e:
            logging.exception(e)

        self.senddatafile = senddatafile
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.connect((address, port))

    def serve(self):
        logging.debug("Connecting... ")
        self.handle(self.socket)

    def handle(self, sock):
        try:
            connection = Connection(sock)

            # send the config file / text first
            connection.send_config_file(np.array(self.hf["Config File"]).tobytes())
            # send the XML header second
            connection.send_metadata(np.array(self.hf["Metadata XML"]).tobytes())
            # send the image data until done
            for k in range(len(self.hf.keys())-2):
                connection.send_image(np.array(self.hf["image_" + str(k)]["header"]).tobytes(),
                                      np.array(self.hf["image_" + str(k)]["attribute"]).tobytes(),
                                      np.array(self.hf["image_" + str(k)]["data"]).tobytes())
            connection.send_close()
        except Exception as e:
            logging.exception(e)
        finally:
            # Encapsulate shutdown in a try block because the socket may have
            # already been closed on the other side
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.hf.close()
            logging.info("\tData at %s is sent to: %s:%d", self.senddatafile, self.socket.getsockname()[0], self.socket.getsockname()[1])
            sock.close()
            logging.info("\tSocket closed")
            # Dataset may not be closed properly if a close message is not received
