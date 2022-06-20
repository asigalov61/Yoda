# -*- coding: utf-8 -*-
"""Sparse_Yoda_Maker.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Ea4TuwVF4OF8B8daQhF3lqVfw0cvTUHq

# Sparse Yoda Maker (ver. 1.0)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

Credit for the Sparse Trainsformer implementation used in this colab goes out @lucidrains https://github.com/lucidrains/sinkhorn-transformer

***

WARNING: This complete implementation is a functioning model of the Artificial Intelligence. Please excercise great humility, care, and respect. https://www.nscai.gov/

***

#### Project Los Angeles

#### Tegridy Code 2022

***

# (Setup Environment)
"""

#@title nvidia-smi gpu check
!nvidia-smi

#@title Install all dependencies (run only once per session)

!git clone https://github.com/asigalov61/tegridy-tools

!pip install sinkhorn_transformer

!pip install torch
!pip install tqdm
!pip install matplotlib

#@title Import all needed modules

print('Loading needed modules. Please wait...')
import os
import random
import tqdm
import numpy as np
import torch
import torch.optim as optim
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

from sinkhorn_transformer import SinkhornTransformerLM
from sinkhorn_transformer.autoregressive_wrapper import AutoregressiveWrapper

if not os.path.exists('/content/Dataset'):
    os.makedirs('/content/Dataset')

print('Loading TMIDIX module...')
os.chdir('/content/tegridy-tools/tegridy-tools')
import TMIDIX

import matplotlib.pyplot as plt

os.chdir('/content/')

"""# (FROM SCRATCH) Download and process MIDI dataset"""

# Commented out IPython magic to ensure Python compatibility.
#@title Download original LAKH/clean_midi MIDI subset (Recommended)

#@markdown Works best stand-alone/as-is for the optimal results
# %cd /content/

!wget 'http://hog.ee.columbia.edu/craffel/lmd/clean_midi.tar.gz'
!tar -xvf 'clean_midi.tar.gz'
!rm 'clean_midi.tar.gz'

# %cd /content/

#@title Process MIDIs to special MIDI dataset with TMIDIX MIDI Processor

#@title Process MIDIs

sorted_or_random_file_loading_order = True # Sorted order is NOT usually recommended
dataset_ratio = 1 # Change this if you need more data


print('TMIDIX MIDI Processor')
print('Starting up...')
###########

files_count = 0

gfiles = []

melody_chords_f = []

###########

print('Loading MIDI files...')
print('This may take a while on a large dataset in particular.')

dataset_addr = "./clean_midi/"
# os.chdir(dataset_addr)
filez = list()
for (dirpath, dirnames, filenames) in os.walk(dataset_addr):
    filez += [os.path.join(dirpath, file) for file in filenames]
print('=' * 70)

if filez == []:
    print('Could not find any MIDI files. Please check Dataset dir...')
    print('=' * 70)

if sorted_or_random_file_loading_order:
    print('Sorting files...')
    filez.sort()
    print('Done!')
    print('=' * 70)
else:
    print('Randomizing file list...')
    random.shuffle(filez)

    
stats = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

print('Processing MIDI files. Please wait...')
for f in tqdm.tqdm(filez[:int(len(filez) * dataset_ratio)]):
    try:
        fn = os.path.basename(f)
        fn1 = fn.split('.')[0]

        files_count += 1

        #print('Loading MIDI file...')
        score = TMIDIX.midi2ms_score(open(f, 'rb').read())

        events_matrix = []

        itrack = 1

        patches = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        patch_map = [[0, 1, 2, 3, 4, 5, 6, 7], # Piano 
                     [24, 25, 26, 27, 28, 29, 30], # Guitar
                     [32, 33, 34, 35, 36, 37, 38, 39], # Bass
                     [40, 41], # Violin
                     [42, 43], # Cello
                     [46], # Harp
                     [56, 57, 58, 59, 60], # Trumpet
                     [71, 72], # Clarinet
                     [73, 74, 75], # Flute
                     [-1], # Fake Drums
                     [52, 53] # Choir
                    ]

        while itrack < len(score):
            for event in score[itrack]:         
                if event[0] == 'note' or event[0] == 'patch_change':
                    events_matrix.append(event)
            itrack += 1

        events_matrix1 = []
        for event in events_matrix:
                if event[0] == 'patch_change':
                    patches[event[2]] = event[3]

                if event[0] == 'note':
                    event.extend([patches[event[3]]])
                    once = False
                    
                    for p in patch_map:
                        if event[6] in p and event[3] != 9: # Except the drums
                            event[3] = patch_map.index(p)
                            once = True
                            
                    if not once and event[3] != 9: # Except the drums
                        event[3] = 0 # All other instruments/patches channel
                        event[5] = max(80, event[5])
                        
                    if event[3] < 11: # We won't write chans 11-16 for now...
                        events_matrix1.append(event)
                        stats[event[3]] += 1

        # recalculating timings
        
        for e in events_matrix1:
            e[1] = int(e[1] / 16)
            e[2] = int(e[2] / 128)
        
        # final processing...

        if len(events_matrix1) > 0:
            
            events_matrix1.sort(key=lambda x: (x[1], x[4]))

            cho = []
            pe = events_matrix1[0]
            melody_chords = []
            for e in events_matrix1:

                time = max(0, min(255, e[1]-pe[1]))
                dur = max(0, min(15, e[2]))
                cha = max(0, min(15, e[3]))
                ptc = max(0, min(127, e[4]))
                vel = max(0, min(127, e[5]))

                melody_chords.append([time, dur, ptc, cha, vel])

                pe = e
            melody_chords_f.append(melody_chords)

        gfiles.append(f)

    except KeyboardInterrupt:
        print('Saving current progress and quitting...')
        break  

    except:
        print('Bad MIDI:', f)
        continue
print('=' * 70)
        
print('Done!')   
print('=' * 70)

print('Resulting Stats:')
print('=' * 70)

print('Piano:', stats[0])
print('Guitar:', stats[1])
print('Bass:', stats[2])
print('Violin:', stats[3])
print('Cello:', stats[4])
print('Harp:', stats[5])
print('Trumpet:', stats[6])
print('Clarinet:', stats[7])
print('Flute:', stats[8])
print('Drums:', stats[9])
print('Choir:', stats[10])

print('=' * 70)

"""# (SAVE/LOAD TRAIN DATA)"""

TMIDIX.Tegridy_Any_Pickle_File_Writer(melody_chords_f, '/content/Sparse_Yoda_Data')

melody_chords_f = TMIDIX.Tegridy_Any_Pickle_File_Reader('/content/Sparse_Yoda_Data')

"""# (PREP INTS)"""

# Process and prep INTs...

randomize_dataset = False

print('=' * 70)
print('Prepping INTs dataset...')

if randomize_dataset:
    print('=' * 70)
    print('Randomizing the dataset...')
    random.shuffle(melody_chords_f)
    print('Done!')
    
print('=' * 70)
print('Processing the dataset...')

train_data1 = []

for chords_list in tqdm.tqdm(melody_chords_f):
    
    train_data1.extend([0]) # Intro/Zero Token
    
    for i in chords_list:

        if i[0] != 0: # This is the chordification line
            train_data1.extend([i[0]]) # start-times
            
        # And this is the main MIDI note line (triple stack)
        main_note = [i[1] + (i[2] * 16) + (i[3] * 16 * 128)] # Main note == [duration / pitch / channel]
        
        if main_note != [0]: # Main note error control...
            train_data1.extend(main_note) # Main note == [duration / pitch / channel]

print('Done!')        
print('=' * 70)
        
print('Total INTs:', len(train_data1))
print('Minimum INT:', min(train_data1))
print('Maximum INT:', max(train_data1))
print('Unique INTs:', len(set(train_data1)))
print('Intro/Zero INTs:', train_data1.count(0))
print('=' * 70)

"""# (TEST)

# Test the resulting INTs dataset...
"""

train_data1[:15]

out = train_data1[:16000]

if len(out) != 0:
    
    song = out
    song_f = []
    time = 0
    dur = 0
    vel = 0
    pitch = 0
    channel = 0
    
    for s in song:
        if s < 256:
            time += s * 16
            
        else:
            channel = s // 16 // 128

            pitch = (s // 16) % 128
            
            dur = ((s % 16) * 128) + 128
            
            # Velocities for each channel:
            if channel == 0:  # Piano     
                vel = 60
            if channel == 1:  # Guitar     
                vel = 70            
            if channel == 2:  # Bass     
                vel = 60            
            if channel == 3:  # Violin
                vel = 90            
            if channel == 4:  # Cello     
                vel = 100
            if channel == 5:  # Harp     
                vel = 80
            if channel == 6:  # Trumpet     
                vel = 100            
            if channel == 7:  # Clarinet     
                vel = 100           
            if channel == 8:  # Flute
                vel = 100                          
            if channel == 9:  # Drums
                vel = 80            
            if channel == 10:  # Choir     
                vel = 110                  
                               
            song_f.append(['note', time, dur, channel, pitch, vel ])

    detailed_stats = TMIDIX.Tegridy_SONG_to_MIDI_Converter(song_f,
                                                        output_signature = 'Yoda',  
                                                        output_file_name = '/content/Yoda-Music-Composition', 
                                                        track_name='Project Los Angeles',
                                                        list_of_MIDI_patches=[0, 24, 32, 40, 42, 46, 56, 71, 73, 0, 53, 0, 0, 0, 0, 0],
                                                        number_of_ticks_per_quarter=500)

    print('Done!')

"""# (TRAIN)

# Train the model
"""

# Setup the model...

# constants


BATCH_SIZE = 4

NUM_BATCHES = int(len(train_data1) / BATCH_SIZE)

GRADIENT_ACCUMULATE_EVERY = 4
LEARNING_RATE = 1e-4
VALIDATE_EVERY  = 100
GENERATE_EVERY  = 200
GENERATE_LENGTH = 64
SEQ_LEN = 4096

# helpers

def cycle(loader):
    while True:
        for data in loader:
            yield data

# instantiate model

model = SinkhornTransformerLM(
    num_tokens = max(train_data1)+1,
    emb_dim = 128,
    dim = 1024, # This should be 1/4 or SEQ_LEN
    depth = 16, # You can bump this to 24 or 32, depending on your dataset size
    max_seq_len = SEQ_LEN,
    heads = 16, # You can bump this to 24 or 32, depending on your dataset size
    bucket_size = 128,
    ff_chunks = 2,
    causal = True,
    reversible = True,
    attn_dropout = 0.1,
    n_local_attn_heads = 4
)
model = AutoregressiveWrapper(model)
model.cuda()

# prepare training data...

X = train_data1
trX, vaX = np.split(X, [len(train_data1)-8192])
data_train, data_val = torch.from_numpy(trX), torch.from_numpy(vaX)

class TextSamplerDataset(Dataset):
    def __init__(self, data, seq_len):
        super().__init__()
        self.data = data
        self.seq_len = seq_len

    def __getitem__(self, index):
        rand_start = torch.randint(0, self.data.size(0) - self.seq_len - 1, (1,))
        full_seq = self.data[rand_start: rand_start + self.seq_len + 1].long()
        return full_seq.cuda()

    def __len__(self):
        return self.data.size(0) // self.seq_len

train_dataset = TextSamplerDataset(data_train, SEQ_LEN)
val_dataset   = TextSamplerDataset(data_val, SEQ_LEN)
train_loader  = cycle(DataLoader(train_dataset, batch_size = BATCH_SIZE))
val_loader    = cycle(DataLoader(val_dataset, batch_size = BATCH_SIZE))

# optimizer

optim = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

# Train...

losses = []
for i in tqdm.tqdm(range(NUM_BATCHES), mininterval=10., desc='Training'):
    model.train()

    for __ in range(GRADIENT_ACCUMULATE_EVERY):
        loss = model(next(train_loader), return_loss = True)
        losses.append(loss.cpu().tolist())
        loss.backward()

    # print(f'Training loss: {loss.item()}')
    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
    optim.step()
    optim.zero_grad()

    if i % VALIDATE_EVERY == 0:
        model.eval()
        with torch.no_grad():
            loss = model(next(val_loader), return_loss = True)
            print(f'Validation loss: {loss.item()}')
            print('Training loss:', losses[-1])

    if i % GENERATE_EVERY == 0:
        model.eval()
        inp = random.choice(val_dataset)[:-1]
        print('Testing...')
        print('Input:', inp[-8:])
        sample = model.generate(inp, GENERATE_LENGTH)
        print('Output:', sample[:8])
        print('Done!')
        print('LOSS:', losses[-1])

    if i % GENERATE_EVERY == 0:
      torch.save(model.state_dict(), '/content/Sparse-Yoda-Trained-Model.pth')
      tr_loss_list = [item for item in losses]
      plt.plot([i for i in range(len(tr_loss_list))] ,tr_loss_list, 'b')
      plt.savefig('/content/Sparse-Yoda-Training-Loss-Graph.png')

"""# Congrats! You did it! :)"""