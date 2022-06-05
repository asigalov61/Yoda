#!/usr/bin/env python
# coding: utf-8

# # Yoda Maker (ver. 1.0)
# 
# ***
# 
# Powered by tegridy-tools TMIDIX Optimus Processors: https://github.com/asigalov61/tegridy-tools
# 
# ***
# 
# Credit for GPT2-RGA code used in this colab goes out @ Sashmark97 https://github.com/Sashmark97/midigen and @ Damon Gwinn https://github.com/gwinndr/MusicTransformer-Pytorch
# 
# ***
# 
# WARNING: This complete implementation is a functioning model of the Artificial Intelligence. Please excercise great humility, care, and respect. https://www.nscai.gov/
# 
# ***
# 
# #### Project Los Angeles
# 
# #### Tegridy Code 2022
# 
# ***

# # (Setup Environment)

# In[ ]:


#@title nvidia-smi gpu check
get_ipython().system('nvidia-smi')


# In[ ]:


#@title Install all dependencies (run only once per session)

get_ipython().system('git clone https://github.com/asigalov61/tegridy-tools')
get_ipython().system('pip install torch')
get_ipython().system('pip install tqdm')
get_ipython().system('pip install matplotlib')


# In[ ]:


#@title Import all needed modules

print('Loading needed modules. Please wait...')
import os
from tqdm import tqdm
import random

if not os.path.exists('/notebooks/Dataset'):
    os.makedirs('/notebooks/Dataset')

print('Loading TMIDIX module...')
os.chdir('/notebooks/tegridy-tools/tegridy-tools')
import TMIDIX

os.chdir('/notebooks/tegridy-tools/tegridy-tools')
from GPT2RGAX import *

import matplotlib.pyplot as plt

os.chdir('/notebooks/')


# # (FROM SCRATCH) Download and process MIDI dataset

# In[ ]:


#@title Download original LAKH/clean_midi MIDI subset (Recommended)

#@markdown Works best stand-alone/as-is for the optimal results
get_ipython().run_line_magic('cd', '/notebooks/')

get_ipython().system("wget 'http://hog.ee.columbia.edu/craffel/lmd/clean_midi.tar.gz'")
get_ipython().system("tar -xvf 'clean_midi.tar.gz'")
get_ipython().system("rm 'clean_midi.tar.gz'")

get_ipython().run_line_magic('cd', '/notebooks/')


# In[ ]:


#@title Process MIDIs to special MIDI dataset with TMIDIX MIDI Processor

#@title Process MIDIs

sorted_or_random_file_loading_order = False # Sorted order is NOT usually recommended
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
for f in tqdm(filez[:int(len(filez) * dataset_ratio)]):
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

                time = min(255, e[1]-pe[1])
                dur = min(15, e[2])
                cha = e[3]
                ptc = min(127, e[4])
                vel = min(127, e[5])

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


# In[ ]:


TMIDIX.Tegridy_Any_Pickle_File_Writer(melody_chords_f, '/notebooks/Yoda_Data')


# In[ ]:


melody_chords_f = TMIDIX.Tegridy_Any_Pickle_File_Reader('/notebooks/Yoda_Data')


# In[ ]:


# Process and prep INTs...

print('=' * 70)
print('Prepping INTs datasets...')

train_data1 = []

for chords_list in tqdm(melody_chords_f):

    for i in chords_list:

        if i[0] != 0: # This is the chordification line
            train_data1.extend([i[0]]) # start-times
            
        # And this is the main MIDI note line (triple stack)
        train_data1.extend([i[1] + (i[2] * 16) + (i[3] * 16 * 128)]) # duration / pitch / channel

print('=' * 70)
print('Done!')        
print('=' * 70)
        
print('Total INTs:', len(train_data1))
print('Minimum INT:', min(train_data1))
print('Maximum INT:', max(train_data1))
print('Unique INTs:', len(set(train_data1)))
print('=' * 70)


# In[ ]:


#@title Load processed INTs datasets

number_of_batches = 16 # Change this to your specs
n_workers = 6 # Change this to your specs
dataset_ratio = 1 # Change this if you want to limit input data
val_dataset_ratio = 0.03 # Change this if you want to limit input data

print('=' * 50)
print('Loading training data...')

train_data = train_data1[:int(len(train_data1) * dataset_ratio)]

val_dataset = train_data[:int(len(train_data) * val_dataset_ratio)]
test_dataset = train_data[:int(len(train_data) * val_dataset_ratio)]

train_list = train_data
val_list = val_dataset
test_list = []
print('=' * 50)

print('Processing INTs datasets...')
train_dataset = EPianoDataset(train_list, max_seq, random_seq)
val_dataset = EPianoDataset(val_list, max_seq)
test_dataset = EPianoDataset(test_list, max_seq)
print('=' * 50)

print('Loading INTs datasets...')
batch_size = number_of_batches
train_loader = DataLoader(train_dataset, batch_size=batch_size, num_workers=n_workers, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, num_workers=n_workers)
test_loader = DataLoader(test_dataset, batch_size=batch_size, num_workers=n_workers)
print('=' * 50)

print('Total INTs in the dataset', len(train_data))
print('Total unique INTs in the dataset', len(set(train_data)))
print('Max INT in the dataset', max(train_data))
print('Min INT in the dataset', min(train_data))
print('=' * 50)

print('Checking datasets shapes...')
print('=' * 50)

print('Train loader')
for x, tgt in train_loader:
    print(f'X shape: {x.shape}')
    print(f'Target shape: {tgt.shape}')
    break
print('=' * 50)

print('Validation loader')
for x, tgt in val_loader:
    print(f'X shape: {x.shape}')
    print(f'Target shape: {tgt.shape}')
    break
print('=' * 50)

print('Test loader')
for x, tgt in test_loader:
    print(f'X shape: {x.shape}')
    print(f'Target shape: {tgt.shape}')
    break
print('=' * 50)

print('Done! Enjoy! :)')
print('=' * 50)


# # Test the resulting INTs dataset...

# In[ ]:


train_data[:15]


# In[ ]:


out = train_data[:16000]

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
                                                        output_file_name = '/notebooks/Yoda-Music-Composition', 
                                                        track_name='Project Los Angeles',
                                                        list_of_MIDI_patches=[0, 24, 32, 40, 42, 46, 56, 71, 73, 0, 53, 0, 0, 0, 0, 0],
                                                        number_of_ticks_per_quarter=500)

    print('Done!')


# # (TRAIN)

# # Train the model

# In[ ]:


#@title Train

DIC_SIZE = max(train_data)+1

config = GPTConfig(DIC_SIZE, 
                   max_seq,
                   dim_feedforward=1024,
                   n_layer=8, 
                   n_head=8, 
                   n_embd=1024,
                   enable_rpr=True,
                   er_len=max_seq)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = GPT(config)

model = nn.DataParallel(model)

model.to(device)

#=====

init_step = 0
lr = LR_DEFAULT_START
lr_stepper = LrStepTracker(d_model, SCHEDULER_WARMUP_STEPS, init_step)
eval_loss_func = nn.CrossEntropyLoss(ignore_index=DIC_SIZE)
train_loss_func = eval_loss_func

opt = Adam(model.parameters(), lr=lr, betas=(ADAM_BETA_1, ADAM_BETA_2), eps=ADAM_EPSILON)
lr_scheduler = LambdaLR(opt, lr_stepper.step)


#===

best_eval_acc        = 0.0
best_eval_acc_epoch  = -1
best_eval_loss       = float("inf")
best_eval_loss_epoch = -1
best_acc_file = '/notebooks/gpt2_rpr_acc.pth'
best_loss_file = '/notebooks/gpt2_rpr_loss.pth'
loss_train, loss_val, acc_val = [], [], []

for epoch in range(0, epochs):
    new_best = False
    
    loss = train(epoch+1, 
                 model, train_loader, 
                 train_loss_func, 
                 opt, 
                 lr_scheduler, 
                 num_iters=-1, 
                 save_checkpoint_steps=4000)
    
    loss_train.append(loss)
    
    eval_loss, eval_acc = eval_model(model, val_loader, eval_loss_func, num_iters=-1)
    loss_val.append(eval_loss)
    acc_val.append(eval_acc)
    
    if(eval_acc > best_eval_acc):
        best_eval_acc = eval_acc
        best_eval_acc_epoch  = epoch+1
        torch.save(model.state_dict(), best_acc_file)
        new_best = True

    if(eval_loss < best_eval_loss):
        best_eval_loss       = eval_loss
        best_eval_loss_epoch = epoch+1
        torch.save(model.state_dict(), best_loss_file)
        new_best = True
    
    if(new_best):
        print("Best eval acc epoch:", best_eval_acc_epoch)
        print("Best eval acc:", best_eval_acc)
        print("")
        print("Best eval loss epoch:", best_eval_loss_epoch)
        print("Best eval loss:", best_eval_loss)


# In[ ]:


# Eval funct to eval separately if needed

#=====

init_step = 0
lr = LR_DEFAULT_START
lr_stepper = LrStepTracker(d_model, SCHEDULER_WARMUP_STEPS, init_step)
eval_loss_func = nn.CrossEntropyLoss(ignore_index=DIC_SIZE)
train_loss_func = eval_loss_func

opt = Adam(model.parameters(), lr=lr, betas=(ADAM_BETA_1, ADAM_BETA_2), eps=ADAM_EPSILON)
lr_scheduler = LambdaLR(opt, lr_stepper.step)


eval_loss, eval_acc = eval_model(model, val_loader, eval_loss_func, num_iters=-1)


# In[ ]:


#@title Plot resulting training loss graph

tr_loss_list = [item for sublist in loss_train for item in sublist]
plt.plot([i for i in range(len(tr_loss_list))] ,tr_loss_list, 'b')
plt.savefig('/notebooks/Yoda-Training-Loss-Graph.png')


# # (SAVE)

# In[ ]:


#@title Save the model

print('Saving the model...')
full_path_to_model_checkpoint = "/notebooks/Yoda-Trained-Model.pth" #@param {type:"string"}
torch.save(model.state_dict(), full_path_to_model_checkpoint)
print('Done!')


# # Congrats! You did it! :)
