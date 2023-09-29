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

    def __init__(self, address, port, savedatafolder):
        logging.info("Starting client and sending data to %s:%d", address, port)
        try:
            logging.debug("Opening folder...")
            self.hf = h5py.File("/home/tunc/PycharmProjects/python-fire-server-base/save/measurement-20230929T152537.hdf5",
                           "r")
        except Exception as e:
            logging.exception(e)

        self.savedatafolder = savedatafolder
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.connect((address, port))

    def serve(self):
        logging.debug("Connecting... ")
        for _ in range(len(self.hf.keys())):
            self.handle(self.socket)

    def handle(self, sock):
        try:
            connection = Connection(sock)

            connection.send_config_file(np.array(self.hf[list(self.hf.keys())[0]]).tobytes())
            for item in saveData:
                hf = item
        except Exception as e:
            logging.exception(e)
        finally:
            # Encapsulate shutdown in a try block because the socket may have
            # already been closed on the other side
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            sock.close()
            logging.info("\tSocket closed")
            # Dataset may not be closed properly if a close message is not received
            if hf:
                try:
                    hf.close()
                    logging.info("\tIncoming data was saved at %s", self.savedatafolder)
                    #oldext = os.path.splitext()[1]
                    #os.rename(file, file+ metadata.measurementInformation.measurementID + oldext)
                except Exception as e:
                    logging.exception(e)

