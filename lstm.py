""" Data processing and LSTM training """
import numpy as np
from keras.layers import LSTM
from keras.layers import Dropout
from keras.layers import Dense
from keras.layers import Activation
from keras.models import Sequential
from keras.utils import np_utils
from keras.callbacks import ModelCheckpoint
import pickle
import glob
from music21 import converter, instrument, note, chord

def train_network():
    notes = get_notes()
    network_input, network_output = prepare_sequences(notes)
    model = create_network(network_input, len(set(notes)))
    train(model, network_input, network_output)

def get_notes():
    """ Get all notes & chords from midi files directory """
    notes = []
    for file in glob.glob("midi_songs/*.mid"):
        midi = converter.parse(file)
        # print("Parsing %s" % file)
        notes_to_parse = None
        try: # file has instrument parts
            s2 = instrument.partitionByInstrument(midi)
            notes_to_parse = s2.parts[0].recurse()
        except: # file has notes in a flat structure
            notes_to_parse = midi.flat.notes
        for element in notes_to_parse:
            if isinstance(element, note.Note):
                notes.append(str(element.pitch))
            elif isinstance(element, chord.Chord):
                notes.append('.'.join(str(n) for n in element.normalOrder))
    with open('data/notes', 'wb') as filepath:
        pickle.dump(notes, filepath)
    return notes

def prepare_sequences(notes):
    sequence_length = 160
    pitchnames = sorted(set(item for item in notes)) # get all pitch names
    note_to_int = dict((note, num) for num, note in enumerate(pitchnames)) # dictionary to map pitches to integers
    network_input = []
    network_output = []
    for i in range(0, len(notes) - sequence_length, 1): # create input sequences and corresponding outputs
        sequence_in = notes[i:i + sequence_length]
        sequence_out = notes[i + sequence_length]
        network_input.append([note_to_int[k] for k in sequence_in])
        network_output.append(note_to_int[sequence_out])
    n_patterns = len(network_input)
    network_input = np.reshape(network_input, (n_patterns, sequence_length, 1)) # reshape the input into a format compatible with LSTM layers
    network_input = network_input / float(len(set(notes))) # normalize input
    network_output = np_utils.to_categorical(network_output)
    return (network_input, network_output)

def create_network(network_input, n_vocab):
    """ create neural network structure """
    model = Sequential()
    model.add(LSTM(
        512,
        input_shape=(network_input.shape[1], network_input.shape[2]),
        return_sequences=True
    ))
    model.add(Dropout(0.4))
    model.add(LSTM(512, return_sequences=True))
    model.add(Dropout(0.4))
    model.add(LSTM(512))
    model.add(Dense(256))
    model.add(Dropout(0.4))
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
    return model

def train(model, network_input, network_output):
    filepath = "weights-improvement-{epoch:02d}-{loss:.4f}-bigger.hdf5"
    checkpoint = ModelCheckpoint(
        filepath,
        monitor='loss',
        verbose=0,
        save_best_only=True,
        mode='min'
    )
    callbacks_list = [checkpoint]
    model.fit(network_input, network_output, epochs=400, batch_size=64, callbacks=callbacks_list)

if __name__ == '__main__':
    train_network()

# code adapted from https://medium.com/m/signin?redirect=https%3A%2F%2Ftowardsdatascience.com%2Fhow-to-generate-music-using-a-lstm-neural-network-in-keras-68786834d4c5%3Fsource%3Dquote_menu--------------------------respond_text&referrer=https%3A%2F%2Ftowardsdatascience.com%2Fhow-to-generate-music-using-a-lstm-neural-network-in-keras-68786834d4c5&originalAction=quote-respond&source=quote_menu--------------------------respond_text