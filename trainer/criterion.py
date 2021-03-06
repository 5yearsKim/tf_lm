import tensorflow as tf

@tf.function
def sparse_categorical_crossentropy(y_true, y_pred):
    loss = tf.keras.losses.sparse_categorical_crossentropy(y_true, y_pred, from_logits=True)
    loss = tf.reduce_mean(loss)
    return loss

@tf.function
def masked_sparse_categorical_crossentropy(y_true, y_pred):
    y_true_masked = tf.boolean_mask(y_true, tf.not_equal(y_true, -1))
    y_pred_masked = tf.boolean_mask(y_pred, tf.not_equal(y_true, -1))
    loss = tf.keras.losses.sparse_categorical_crossentropy(y_true_masked, y_pred_masked, from_logits=True)
    loss = tf.math.reduce_mean(loss)
    return loss

@tf.function
def masked_cce(y_true, y_pred):
    mask = tf.cast(y_true >= 0, dtype=tf.float32)
    y_true = tf.math.abs(y_true)
    loss = tf.keras.losses.sparse_categorical_crossentropy(y_true, y_pred, from_logits=True)
    loss = tf.math.multiply(loss, mask)
    loss = tf.math.reduce_sum(loss) / (tf.math.reduce_sum(mask) + 1e-6)
    return loss

@tf.function
def pad_masked_cce(y_true, y_pred):
    mask = tf.cast(y_true > 0, dtype=tf.float32)
    y_true = tf.math.abs(y_true)
    loss = tf.keras.losses.sparse_categorical_crossentropy(y_true, y_pred, from_logits=True)
    loss = tf.math.multiply(loss, mask)
    loss = tf.math.reduce_sum(loss) / (tf.math.reduce_sum(mask) + 1e-6)
    return loss

# @tf.function
# def masked_cce(y_true, y_pred):
#     mask = tf.cast(y_true >= 0, dtype=tf.float32)
#     y_true = tf.one_hot(y_true, y_pred.shape[-1], off_value=0.0)
#     loss = tf.keras.losses.categorical_crossentropy(y_true, y_pred, from_logits=True)
#     loss = tf.math.multiply(loss, mask)
#     loss = tf.math.reduce_sum(loss) / (tf.math.reduce_sum(mask) + 1e-6)
#     return loss