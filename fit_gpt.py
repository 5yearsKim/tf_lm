import tensorflow as tf
from transformers import TFGPT2LMHeadModel, GPT2Config 
from dataloader.load_data import read_gpt_tfrecord, read_ctx_tfrecord
from dataloader.tfrecord_utils import load_from_gcs
from glob import glob
from config import *
from google.cloud import storage
from distribute.utils import setup_strategy
from trainer.criterion import pad_masked_cce

from tensorflow.keras.callbacks import ReduceLROnPlateau, ModelCheckpoint

strategy, num_replica = setup_strategy()
batch_size = (BS // num_replica) * num_replica
if num_replica == 1:
    batch_size = 1

def create_model(max_len=256):
    config = GPT2Config(**GPT_SMALL_CONFIG)
    input_ids = tf.keras.layers.Input(shape=(max_len,), dtype='int32')
    gpt = TFGPT2LMHeadModel(config)
    out = gpt(input_ids).logits
    model = tf.keras.Model(inputs=input_ids, outputs=out)
    if IS_LOAD:
        load_path = LOAD_PATH 
        model.load_weights(load_path)
        print(f'loaded from {load_path}!!')
    # model = TFGPT2LMHeadModel(config)
    optimizer = tf.keras.optimizers.Adam(learning_rate=LR)
    model.compile(
        optimizer=optimizer,
        # loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        loss=pad_masked_cce
    )
    return model

with strategy.scope():
    model = create_model()


# train_from = glob('data/everytime/*.tfrecord', recursive=True)
# train_from = load_from_gcs('nlp-pololo', prefix=['gpt_tfrecord/everytime/'])
train_from = load_from_gcs('nlp-pololo', prefix=['context_tfrecord/everytime/', 'context_tfrecord/aihub_sns', 'context_tfrecord/kakao'],\
                    sort_key=lambda path: 0 if 'everytime' in path else 1)
# train_from = train_from[:1]
print(train_from)

# dset = read_gpt_tfrecord(train_from).shuffle(buffer_size=20000)
dset = read_ctx_tfrecord(train_from, with_mask=True).shuffle(buffer_size=20000)
dset = dset.padded_batch(batch_size, padded_shapes=(MAX_SEQ_LEN, MAX_SEQ_LEN),\
    padding_values=tf.constant(0, dtype=tf.int64), drop_remainder=True)

skip_point = 1000 
train_set, val_set = dset.skip(skip_point), dset.take(skip_point)
print('splitting train/val set..')

train_set = strategy.experimental_distribute_dataset(train_set.repeat())
val_set = strategy.experimental_distribute_dataset(val_set)

train_steps = 2000000 // BS + 1
val_steps = skip_point 


callbacks = [
    # EarlyStopping(monitor='val_loss', patience=10), 
    # ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=_learning_rate * 0.05),
    ModelCheckpoint(f"ckpts/best.h5",
        monitor='val_loss', 
        save_best_only=True,
        save_weights_only=True,
        mode='auto')
    # WandbCallback(),
    ]


print(f'train batch size={batch_size}, lr={LR}')
model.fit(train_set,
    epochs=EPOCHS,
    steps_per_epoch=train_steps,
    callbacks=callbacks,
    validation_data=val_set,
    validation_steps=val_steps
    )