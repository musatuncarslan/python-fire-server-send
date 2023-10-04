import constants
import ismrmrd
import ctypes
import threading

import logging
import socket

class Connection:
    def __init__(self, socket):
        self.socket         = socket
        self.is_exhausted   = False
        self.sentAcqs       = 0
        self.sentImages     = 1
        self.sentWaveforms  = 0
        self.recvAcqs       = 0
        self.recvImages     = 0
        self.recvWaveforms  = 0
        self.lock           = threading.Lock()
        self.handlers       = {
            constants.MRD_MESSAGE_CONFIG_FILE:         self.read_config_file,
            constants.MRD_MESSAGE_CONFIG_TEXT:         self.read_config_text,
            constants.MRD_MESSAGE_METADATA_XML_TEXT:   self.read_metadata,
            constants.MRD_MESSAGE_CLOSE:               self.read_close,
            constants.MRD_MESSAGE_TEXT:                self.read_text,
            constants.MRD_MESSAGE_ISMRMRD_ACQUISITION: self.read_acquisition,
            constants.MRD_MESSAGE_ISMRMRD_WAVEFORM:    self.read_waveform,
            constants.MRD_MESSAGE_ISMRMRD_IMAGE:       self.read_image
        }

    def send_logging(self, level, contents):
        try:
            formatted_contents = "%s %s" % (level, contents)
        except:
            logging.warning("Unsupported logging level: " + level)
            formatted_contents = contents

        self.send_text(formatted_contents)

    def __iter__(self):
        while not self.is_exhausted:
            yield self.next()

    def __next__(self):
        return self.next()

    def read(self, nbytes):
        return self.socket.recv(nbytes, socket.MSG_WAITALL)

    def next(self):
        with self.lock:
            id = self.read_mrd_message_identifier()

            if (self.is_exhausted == True):
                return

            handler = self.handlers.get(id, lambda: Connection.unknown_message_identifier(id))
            return handler()

    @staticmethod
    def unknown_message_identifier(identifier):
        logging.error("Received unknown message type: %d", identifier)
        raise StopIteration

    def read_mrd_message_identifier(self):
        try:
            identifier_bytes = self.read(constants.SIZEOF_MRD_MESSAGE_IDENTIFIER)
        except ConnectionResetError:
            logging.error("Connection closed unexpectedly")
            self.is_exhausted = True
            return

        if (len(identifier_bytes) == 0):
            self.is_exhausted = True
            return

        return constants.MrdMessageIdentifier.unpack(identifier_bytes)[0]

    def read_mrd_message_length(self):
        length_bytes = self.read(constants.SIZEOF_MRD_MESSAGE_LENGTH)
        return constants.MrdMessageLength.unpack(length_bytes)[0]

    # ----- MRD_MESSAGE_CONFIG_FILE (1) ----------------------------------------
    # This message contains the file name of a configuration file used for 
    # image reconstruction/post-processing.  The file must exist on the server.
    # Message consists of:
    #   ID               (   2 bytes, unsigned short)
    #   Config file name (1024 bytes, char          )
    def send_config_file(self, filename):
        with self.lock:
            logging.info("--> Sending MRD_MESSAGE_CONFIG_FILE (1)")
            self.socket.send(constants.MrdMessageIdentifier.pack(constants.MRD_MESSAGE_CONFIG_FILE))
            self.socket.send(constants.MrdMessageConfigurationFile.pack(filename))

    def read_config_file(self):
        logging.info("<-- Received MRD_MESSAGE_CONFIG_FILE (1)")
        config_file_bytes = self.read(constants.SIZEOF_MRD_MESSAGE_CONFIGURATION_FILE)
        config_file = constants.MrdMessageConfigurationFile.unpack(config_file_bytes)[0].decode("utf-8").split('\x00', 1)[0] # unpack, decode, and strip off null terminators in fixed 1024 size
        logging.debug("\t" + config_file)
        return 1, config_file, config_file_bytes

    # ----- MRD_MESSAGE_CONFIG_TEXT (2) --------------------------------------
    # This message contains the configuration information (text contents) used 
    # for image reconstruction/post-processing.  Text is null-terminated.
    # Message consists of:
    #   ID               (   2 bytes, unsigned short)
    #   Length           (   4 bytes, uint32_t      )
    #   Config text data (  variable, char          )
    def send_config_text(self, contents):
        with self.lock:
            logging.info("--> Sending MRD_MESSAGE_CONFIG_TEXT (2)")
            self.socket.send(constants.MrdMessageIdentifier.pack(constants.MRD_MESSAGE_CONFIG_TEXT))
            contents_with_nul = '%s\0' % contents # Add null terminator
            self.socket.send(constants.MrdMessageLength.pack(len(contents_with_nul)))
            self.socket.send(contents_with_nul)

    def read_config_text(self):
        logging.info("<-- Received MRD_MESSAGE_CONFIG_TEXT (2)")
        length = self.read_mrd_message_length()
        config_bytes = self.read(length)
        config = config_bytes.decode("utf-8").split('\x00',1)[0]  # Strip off null terminator
        logging.debug("    " + config)
        return 2, config, config_bytes

    # ----- MRD_MESSAGE_METADATA_XML_TEXT (3) -----------------------------------
    # This message contains the metadata for the entire dataset, formatted as
    # MRD XML flexible data header text.  Text is null-terminated.
    # Message consists of:
    #   ID               (   2 bytes, unsigned short)
    #   Length           (   4 bytes, uint32_t      )
    #   Text xml data    (  variable, char          )
    def send_metadata(self, contents):
        with self.lock:
            logging.info("--> Sending MRD_MESSAGE_METADATA_XML_TEXT (3)")
            self.socket.send(constants.MrdMessageIdentifier.pack(constants.MRD_MESSAGE_METADATA_XML_TEXT))
            self.socket.send(constants.MrdMessageLength.pack(len(contents)))
            self.socket.send(contents)

    def read_metadata(self):
        logging.info("<-- Received MRD_MESSAGE_METADATA_XML_TEXT (3)")
        length = self.read_mrd_message_length()
        metadata_bytes = self.read(length)
        metadata = metadata_bytes.decode("utf-8").split('\x00',1)[0]  # Strip off null teminator
        return 3, metadata, metadata_bytes

    # ----- MRD_MESSAGE_CLOSE (4) ----------------------------------------------
    # This message signals that all data has been sent (either from server or client).
    def send_close(self):
        with self.lock:
            logging.info("--> Sending MRD_MESSAGE_CLOSE (4)")
            self.socket.send(constants.MrdMessageIdentifier.pack(constants.MRD_MESSAGE_CLOSE))

    def read_close(self):
        logging.info("<-- Received MRD_MESSAGE_CLOSE (4)")
        self.is_exhausted = True
        return

    # ----- MRD_MESSAGE_TEXT (5) -----------------------------------
    # This message contains arbitrary text data.
    # Message consists of:
    #   ID               (   2 bytes, unsigned short)
    #   Length           (   4 bytes, uint32_t      )
    #   Text data        (  variable, char          )
    def send_text(self, contents):
        with self.lock:
            logging.info("--> Sending MRD_MESSAGE_TEXT (5)")
            logging.info("    %s", contents)
            self.socket.send(constants.MrdMessageIdentifier.pack(constants.MRD_MESSAGE_TEXT))
            contents_with_nul = '%s\0' % contents # Add null terminator
            self.socket.send(constants.MrdMessageLength.pack(len(contents_with_nul.encode())))
            self.socket.send(contents_with_nul.encode())

    def read_text(self):
        logging.info("<-- Received MRD_MESSAGE_TEXT (5)")
        length = self.read_mrd_message_length()
        text_bytes = self.read(length)
        text = text_bytes.decode("utf-8").split('\x00',1)[0]  # Strip off null teminator
        logging.info("    %s", text)
        return 5, text, text_bytes

    # ----- MRD_MESSAGE_ISMRMRD_ACQUISITION (1008) -----------------------------
    # This message contains raw k-space data from a single readout.
    # Message consists of:
    #   ID               (   2 bytes, unsigned short)
    #   Fixed header     ( 340 bytes, mixed         )
    #   Trajectory       (  variable, float         )
    #   Raw k-space data (  variable, float         )
    def send_acquisition(self, acquisition):
        with self.lock:
            self.sentAcqs += 1
            if (self.sentAcqs == 1) or (self.sentAcqs % 100 == 0):
                logging.info("--> Sending MRD_MESSAGE_ISMRMRD_ACQUISITION (1008) (total: %d)", self.sentAcqs)

            self.socket.send(constants.MrdMessageIdentifier.pack(constants.MRD_MESSAGE_ISMRMRD_ACQUISITION))
            acquisition.serialize_into(self.socket.send)

    def read_acquisition(self):
        self.recvAcqs += 1
        if (self.recvAcqs == 1) or (self.recvAcqs % 100 == 0):
            logging.info("<-- Received MRD_MESSAGE_ISMRMRD_ACQUISITION (1008) (total: %d)", self.recvAcqs)

        acq = ismrmrd.Acquisition.deserialize_from(self.read)

        return acq

    # ----- MRD_MESSAGE_ISMRMRD_IMAGE (1022) -----------------------------------
    # This message contains a single [x y z cha] image.
    # Message consists of:
    #   ID               (   2 bytes, unsigned short)
    #   Fixed header     ( 198 bytes, mixed         )
    #   Attribute length (   8 bytes, uint_64       )
    #   Attribute data   (  variable, char          )
    #   Image data       (  variable, variable      )
    def send_image(self, head, attribute, imageData):
        with self.lock:
            logging.info("--> Sending MRD_MESSAGE_ISMRMRD_IMAGE (1022) for image: %d", self.sentImages)
            # Explicit version of serialize_into() for more verbose debugging
            self.socket.send(constants.MrdMessageIdentifier.pack(constants.MRD_MESSAGE_ISMRMRD_IMAGE))
            self.socket.send(head)
            self.socket.send(constants.MrdMessageAttribLength.pack(len(attribute)))
            self.socket.send(attribute)
            self.socket.send(imageData)
            self.sentImages += 1

    def read_image(self):
        self.recvImages += 1
        logging.info("<-- Received MRD_MESSAGE_ISMRMRD_IMAGE (1022)")
        # return ismrmrd.Image.deserialize_from(self.read)

        # Explicit version of deserialize_from() for more verbose debugging
        logging.info("\tReading in %d bytes of image header", ctypes.sizeof(ismrmrd.ImageHeader))
        header_bytes = self.read(ctypes.sizeof(ismrmrd.ImageHeader))

        attribute_length_bytes = self.read(ctypes.sizeof(ctypes.c_uint64))
        attribute_length = ctypes.c_uint64.from_buffer_copy(attribute_length_bytes)
        logging.debug("\tReading in %d bytes of attributes", attribute_length.value)

        attribute_bytes = self.read(attribute_length.value)
        #if (attribute_length.value > 25000):
        #    logging.debug("   Attributes (truncated): %s", attribute_bytes[0:24999].decode('utf-8'))
        #else:
        #    logging.debug("   Attributes: %s", attribute_bytes.decode('utf-8'))

        image = ismrmrd.Image(header_bytes, attribute_bytes.decode('utf-8').split('\x00',1)[0])  # Strip off null teminator

        logging.info("\tImage is size %d x %d x %d with %d channels of type %s", image.getHead().matrix_size[0], image.getHead().matrix_size[1], image.getHead().matrix_size[2], image.channels, ismrmrd.get_dtype_from_data_type(image.data_type))
        def calculate_number_of_entries(nchannels, xs, ys, zs):
            return nchannels * xs * ys * zs

        nentries = calculate_number_of_entries(image.channels, *image.matrix_size)
        nbytes = nentries * ismrmrd.get_dtype_from_data_type(image.data_type).itemsize

        logging.debug("\tReading in %d bytes of image data", nbytes)
        data_bytes = self.read(nbytes)

        #image.data.ravel()[:] = np.frombuffer(data_bytes, dtype=ismrmrd.get_dtype_from_data_type(image.data_type)) # this is not necessary for saving purposes

        return 1022, image, header_bytes, attribute_bytes, data_bytes

    # ----- MRD_MESSAGE_ISMRMRD_WAVEFORM (1026) -----------------------------
    # This message contains abitrary (e.g. physio) waveform data.
    # Message consists of:
    #   ID               (   2 bytes, unsigned short)
    #   Fixed header     ( 240 bytes, mixed         )
    #   Waveform data    (  variable, uint32_t      )
    def send_waveform(self, waveform):
        with self.lock:
            self.sentWaveforms += 1
            if (self.sentWaveforms == 1) or (self.sentWaveforms % 100 == 0):
                logging.info("--> Sending MRD_MESSAGE_ISMRMRD_WAVEFORM (1026) (total: %d)", self.sentWaveforms)

            self.socket.send(constants.MrdMessageIdentifier.pack(constants.MRD_MESSAGE_ISMRMRD_WAVEFORM))
            waveform.serialize_into(self.socket.send)

    def read_waveform(self):
        self.recvWaveforms += 1
        if (self.recvWaveforms == 1) or (self.recvWaveforms % 100 == 0):
            logging.info("<-- Received MRD_MESSAGE_ISMRMRD_WAVEFORM (1026) (total: %d)", self.recvWaveforms)
        waveform = ismrmrd.Waveform.deserialize_from(self.read)
        return waveform

