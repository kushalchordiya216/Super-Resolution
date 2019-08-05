from keras import layers as L
import cv2
import numpy as np
from keras.models import Model
from tqdm import tqdm
import keras
import os

epochs = 400
batch_size = 100

# load data
print("Loading images")
X_train = []
iterator = tqdm(os.listdir('../celeba_resized'))
for file in iterator:
    img_path = str('../celeba_resized/'+str(file))
    pic = cv2.imread(img_path)
    X_train.append(pic)
    if len(X_train) == 100000:
        iterator.close()
        break

X_train = np.array(X_train)
#X_train = X_train.astype(float)/255.0


def ResBlock(x, filters):
    res = x
    x = L.Conv2D(filters=filters, kernel_size=(3, 3), padding='same')(x)
    x = L.ReLU()(x)
    x = L.Conv2D(filters=filters, kernel_size=(3, 3), padding='same')(x)
    x = L.ReLU()(x)
    x = L.Add()([x, res])
    return x


def create_generator():
    img = L.Input(shape=(100,))
    x = L.Dense(units=64*64*3)(img)
    x = L.Reshape(target_shape=(64, 64, 3))(x)
    x = L.Conv2D(filters=8, kernel_size=(3, 3),
                 padding='same', activation='relu')(x)
    x = ResBlock(x, 8)
    x = ResBlock(x, 8)
    x = ResBlock(x, 8)
    x = L.Dropout(0.2)(x)
    x = L.Conv2D(filters=16, kernel_size=(3, 3),
                 padding='same', activation='relu')(x)
    x = ResBlock(x, 16)
    x = ResBlock(x, 16)
    x = ResBlock(x, 16)
    x = L.Dropout(0.2)(x)
    x = L.Conv2D(filters=32, kernel_size=(3, 3),
                 padding='same', activation='relu')(x)
    x = ResBlock(x, 32)
    x = ResBlock(x, 32)
    x = ResBlock(x, 32)
    x = L.Dropout(0.2)(x)

    x = L.Conv2D(filters=3, kernel_size=(3, 3),
                 padding='same', activation='relu')(x)
    gen = Model(inputs=img, outputs=x)
    gen.compile(loss=keras.losses.binary_crossentropy,
                optimizer=keras.optimizers.adamax(0.001))
    return gen


def create_discriminator():
    inp = L.Input(shape=(64, 64, 3,))

    x = L.Conv2D(filters=8, kernel_size=(3, 3), padding='valid')(inp)
    x = L.ReLU()(x)
    x = L.Dropout(0.2)(x)
    x = L.Conv2D(filters=16, kernel_size=(3, 3), padding='valid')(x)
    x = L.ReLU()(x)
    x = L.Dropout(0.2)(x)
    x = L.Conv2D(filters=32, kernel_size=(3, 3), padding='valid')(x)
    x = L.ReLU()(x)
    x = L.Dropout(0.2)(x)
    x = L.Flatten()(x)
    x = L.Dense(1, activation='sigmoid')(x)
    dis = Model(inputs=inp, outputs=x)
    dis.compile(loss=keras.losses.binary_crossentropy,
                optimizer=keras.optimizers.adamax(0.001))
    return dis


def create_gan(discriminator, generator):
    discriminator.trainable = False
    gan_input = L.Input(shape=(100,))
    x = generator(gan_input)
    gan_output = discriminator(x)
    gan = Model(inputs=gan_input, outputs=gan_output)
    gan.compile(loss=keras.losses.binary_crossentropy,
                optimizer=keras.optimizers.adamax(0.001))
    return gan


generator = create_generator()
discriminator = create_discriminator()
gan = create_gan(discriminator, generator)

# print(generator.summary())
# print(discriminator.summary())
print(gan.summary())

for e in range(1, epochs+1):
    print("Epoch %d" % e)
    for _ in tqdm(range(batch_size)):
        noise = np.random.normal(0, 1, [batch_size, 100])
        generated_images = generator.predict(noise)
        image_batch = X_train[np.random.randint(
            low=0, high=X_train.shape[0], size=batch_size)]
        X = np.concatenate([image_batch, generated_images])
        y_dis = np.zeros(2*batch_size)
        y_dis[:batch_size] = 0.9
        discriminator.trainable = True
        discriminator_loss = discriminator.train_on_batch(X, y_dis)
        noise = np.random.normal(0, 1, [batch_size, 100])
        y_gen = np.ones(batch_size)
        discriminator.Trainable = False
        gan_loss = gan.train_on_batch(noise, y_gen)
    pr = generator.predict(np.random.normal(0, 1, [1, 100]), batch_size=1)
    pr = pr.reshape(64, 64, 3)
    print(pr)
    pr = pr.astype(int)
    cv2.imwrite('pr'+str(e)+'.jpg', pr)
    print("Discriminator loss="+str(discriminator_loss))
    print("GAN loss="+str(gan_loss))
    if e % 10 == 0:
        generator.save('generatorep'+str(e)+'.hdf5')
generator.save('generator1.hdf5')
discriminator.save('discriminator1.hdf5')
pr = generator.predict(np.random.normal(0, 1, [1, 100]), batch_size=1)
pr = pr.reshape(64, 64, 3)
pr = pr.astype(int)
print(pr)
cv2.imwrite('pr.jpg', pr)
