# -*- coding: utf-8 -*-
"""Fabric_RESNET.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12vO1cU0OgzJ98hjoFZnzHHvPj3Y2GsF-
"""

pip install bayesian-optimization

import tensorflow as tf
import pandas as pd
import numpy as np
import itertools
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense,Conv2D,MaxPool2D,Flatten,Dropout,BatchNormalization,Activation
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
from tensorflow.keras.utils import plot_model
from bayes_opt import BayesianOptimization
from tensorflow.keras.utils import load_img,img_to_array
from keras.applications import resnet
from sklearn.metrics import classification_report
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import confusion_matrix

from google.colab import drive
drive.mount('/content/drive')

physical_devices = tf.config.experimental.list_physical_devices('GPU')
print("Num GPUs Available: ", len(physical_devices))
tf.config.experimental.set_memory_growth(physical_devices[0], True)

train_directory='/content/drive/MyDrive/Thesis/Old Fabric Defect Dataset/train'
val_directory='/content/drive/MyDrive/Thesis/Old Fabric Defect Dataset/valid'
test_directory='/content/drive/MyDrive/Thesis/Old Fabric Defect Dataset/test'
train_datagen=ImageDataGenerator(rescale=1/255)
val_datagen=ImageDataGenerator(rescale=1/255)
test_datagen=ImageDataGenerator(rescale=1/255)

"""import numpy as np

def gray_to_rgb(img):
    return np.repeat(img, 3, 2)

generator = ImageDataGenerator(..., preprocessing_function=gray_to_rgb)
train_gen = generator.flow_from_directory(color_mode='grayscale', ...)
"""

train_generator=train_datagen.flow_from_directory(train_directory,
                                                 target_size=(224,224),
                                                 color_mode='rgb',
                                                 class_mode='sparse',batch_size=256)

val_generator=val_datagen.flow_from_directory(val_directory,
                                                 target_size=(224,224),
                                                 color_mode='rgb',
                                                 class_mode='sparse',batch_size=256)

test_generator=test_datagen.flow_from_directory(test_directory,
                                                 target_size=(224,224)    ,
                                                 color_mode='rgb',
                                                 class_mode='sparse',batch_size=256)

train_generator.class_indices

ResNet = resnet.ResNet152
convlayer=ResNet(input_shape=(224,224,3),weights='imagenet',include_top=False)
for layer in convlayer.layers:
    layer.trainable=False
model2=Sequential()
model2.add(convlayer)
model2.add(Dropout(0.5))
model2.add(Flatten())
model2.add(BatchNormalization())
model2.add(Dense(2048,kernel_initializer='he_uniform'))
model2.add(BatchNormalization())
model2.add(Activation('relu'))
model2.add(Dropout(0.5))
model2.add(Dense(1024,activation='relu'))
model2.add(BatchNormalization())
model2.add(Activation('relu'))
model2.add(Dropout(0.5))
model2.add(Dense(6,activation='sigmoid'))
print(model2.summary())
opt=tf.keras.optimizers.Adamax(learning_rate=0.001)
model2.compile(loss='sparse_categorical_crossentropy',metrics=['accuracy'],optimizer=opt)

plot_model(model2, to_file='resnet_architecture.png')

history=model2.fit(train_generator,validation_data=test_generator,
         epochs=50)

max_accuracy = max(history.history['val_accuracy'])
epoch = history.history['val_accuracy'].index(max_accuracy)
print('Max Accuracy: ',max_accuracy)
print('Epoch: ', epoch)

plt.figure(figsize=(8, 6))
for c in ['loss', 'val_loss']:
    plt.plot(
        history.history[c], label=c)
plt.legend()
plt.xlabel('Epoch')
plt.ylabel('Average Negative Log Likelihood')
plt.title('Training and Validation Losses')

plt.figure(figsize=(8, 6))
for c in ['accuracy', 'val_accuracy']:
    plt.plot(history.history[c], label=c)
plt.legend()
plt.xlabel('Epoch')
plt.ylabel('Average Accuracy')
plt.title('Training and Validation Accuracy')

"""# **Precision, Recall, and F1 Score**"""

y_true = test_generator.classes
predictions = model2.predict(x=test_generator, steps=len(test_generator), verbose=0)
y_pred = predictions.argmax(axis=1)

#calculating precision and reall
cm = confusion_matrix(y_true, y_pred)
true_pos = np.diag(cm)
false_pos = np.sum(cm, axis=0) - true_pos
false_neg = np.sum(cm, axis=1) - true_pos

precision = np.average(true_pos / (true_pos + false_pos))
recall = np.average(true_pos / (true_pos + false_neg))
F1 = 2 * (precision * recall) / (precision + recall)

print('Precision: ',precision)
print('Recall: ',recall)
print('F1 Score: ',F1)

"""# **Bayesian Optimizer**"""

# Define the objective function for Bayesian optimization
def objective(learning_rate, dropout_rate):
    # Update the model with the new hyperparameters
    optimizer.learning_rate = learning_rate
    model2.layers[-5].rate = dropout_rate
    model2.layers[-7].rate = dropout_rate

    # Train the model
    history = model2.fit(x=train_generator,
            validation_data=test_generator,
            epochs=20,
            verbose=2
)

    # Return the validation accuracy for optimization
    return max(history.history['val_accuracy'])

# Define the parameter ranges for Bayesian optimization
pbounds = {'learning_rate': (1e-6, 1e-2),
           'dropout_rate': (0.0, 0.5)}

# Run Bayesian optimization
optimizer = BayesianOptimization(f=objective, pbounds=pbounds, verbose=2)
optimizer.maximize(init_points=2, n_iter=2)

# Get the best hyperparameters
best_params = optimizer.max['params']
best_learning_rate = best_params['learning_rate']
best_dropout_rate = best_params['dropout_rate']

# Update the model with the best hyperparameters
optimizer.learning_rate = best_learning_rate
model2.layers[-5].rate = best_dropout_rate
model2.layers[-7].rate = best_dropout_rate

# Train the model with the best hyperparameters
history = model2.fit(x=train_generator,
            validation_data=test_generator,
            epochs=20,
            verbose=2
)

plt.plot(history.history['accuracy'],c='orange')
plt.plot(history.history['val_accuracy'],c='blue')
plt.title('Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['train','validation'],loc='lower right')

plt.plot(history.history['loss'],c='orange')
plt.plot(history.history['val_loss'],c='blue')
plt.title('Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['train','validation'],loc='upper right')



"""# **Precision, Recall, and F1 Score**"""

y_true = test_generator.classes
predictions = model2.predict(x=test_generator, steps=len(test_generator), verbose=0)
y_pred = predictions.argmax(axis=1)

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
            horizontalalignment="center",
            color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')

#calculating precision and reall
cm = confusion_matrix(y_true, y_pred)
true_pos = np.diag(cm)
false_pos = np.sum(cm, axis=0) - true_pos
false_neg = np.sum(cm, axis=1) - true_pos

precision = np.average(true_pos / (true_pos + false_pos))
recall = np.average(true_pos / (true_pos + false_neg))
F1 = 2 * (precision * recall) / (precision + recall)

print('Precision: ',precision)
print('Recall: ',recall)
print('F1 Score: ',F1)

plot_confusion_matrix(cm=cm, classes=['Hole','Horizontal','Vertical'], title='Confusion Matrix')

