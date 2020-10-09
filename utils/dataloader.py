import os
from PIL import Image
import torch
from torchvision.transforms import Resize, ToTensor
from torch.utils.data import Dataset, DataLoader, random_split
from pytorch_lightning import LightningDataModule


def recursiveResize(img: Image, factor: int = 2):
    """
    Recursively resizes an image by down scaling by 2,
    repeats this for factor times
    Args:
        img (PIL.Image): image to be resized
        factor (int): factor by which resizing is to take place. eg. if factor is 2, image will be downscaled
        to half it's size twice, thereby final image with be 1/4th the original image size
    Returns:

    """
    for _ in range(factor):
        height, width = img.size
        print(height, width)
        resize = Resize((int(height / 2), int(width / 2)), interpolation=Image.BICUBIC)
        img = resize(img)
    return img


class SRDataset(Dataset):
    def __init__(self, data_dir: str = 'images/', img_size: int = 128):
        super(SRDataset, self).__init__()
        self.img_dir = data_dir
        self.filenames = os.listdir(self.img_dir)
        self.toTensor = ToTensor()
        self.setSize = Resize((img_size, img_size), interpolation=Image.BICUBIC)

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, index):
        img = Image.open(self.filenames[index])
        img = self.setSize(img)
        lr_img = recursiveResize(img, 2)
        hr_img = img
        interpolated_img = self.setSize(lr_img)
        lr_img, hr_img, interpolated_img = self.toTensor(lr_img), self.toTensor(hr_img), self.toTensor(interpolated_img)
        return lr_img, hr_img, interpolated_img


class SRDataLoader(LightningDataModule):
    def __init__(self, data_dir: str = "images/", batch_size: int = 32, img_size: int = 128):
        super().__init__()
        self.batch_size = batch_size
        self.data_dir = data_dir
        self.img_size = img_size
        self.train, self.val, self.test = None, None, None

    def setup(self, stage=None):
        self.train, self.val, self.test = random_split(
            SRDataset(data_dir=self.data_dir, img_size=self.img_size), lengths=[180000, 2059, 20000], generator=torch.Generator().manual_seed(0))

    def train_dataloader(self, *args, **kwargs):
        return DataLoader(self.train, batch_size=self.batch_size, num_workers=4, drop_last=True,
                          pin_memory=True)

    def val_dataloader(self, *args, **kwargs):
        return DataLoader(self.val, batch_size=self.batch_size, num_workers=4, pin_memory=True, drop_last=True)

    def test_dataloader(self, *args, **kwargs):
        return DataLoader(self.test, batch_size=self.batch_size, num_workers=4, pin_memory=True, drop_last=True)