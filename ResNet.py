from DataLoad import DataLoad
from DataLoad import load_file_list
from DataSet import CatDogDataSet
from DataSet import CatDogDataSet_files
from train_test import train
from train_test import test

from torch.utils.data import DataLoader
import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F

from torchvision import models

import torch.optim as optim

import numpy as np
import os

from Model_cut import load_object
from Model_cut import save_object

class my_ResNet(nn.Module):
    def __init__(self, requeires_grad=False):
        super(my_ResNet, self).__init__()
        self.net = models.resnet18(pretrained=True)

        if not requeires_grad:
            for param in self.net.parameters():
                param.requires_grad = False

        in_feature_num = self.net.fc.in_features
        self.net.fc = nn.Linear(in_feature_num, 2)



    def forward(self, input):
        return self.net(input)


def main(sampled = False, run_name=''):
    batch_size = 50
    class_num = 2
    num_workers = 20

    learning_rate = 0.0001 # default 0.001
    momentum = 0.9  # default 0.9

    file_read_type = True

    '''
    net = models.resnet18(pretrained=True)
    print(net)

    for param in net.parameters():
        param.requires_grad = False

    in_feature_num = net.fc.in_features

    net.fc = nn.Linear(in_feature_num, 2)
    '''

    net = my_ResNet(requeires_grad=False)

    if file_read_type:
        images_train_list, labels_train, images_val_list, labels_val, image_test_list, test_filenames = load_file_list(
            sampled=sampled)
    else:
        loader = DataLoad(sampled=sampled, model_type='resnet')
        images_train, labels_train, images_val, labels_val, image_test, test_filenames = loader.get_data()

        images_train = torch.from_numpy(images_train)
        images_val = torch.from_numpy(images_val)
        image_test = torch.from_numpy(image_test)

    labels_train = torch.from_numpy(labels_train)
    labels_val = torch.from_numpy(labels_val)

    if file_read_type:
        train_dataset_file = CatDogDataSet_files(images_train_list, labels_train, sampled, model_type='resnet')
    else:
        train_dataset = CatDogDataSet(images_train, labels_train)

    print(net)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(net.parameters(), lr=learning_rate, momentum=momentum)
    # optimizer = optim.Adam(net.parameters(), lr=learning_rate)

    if not os.path.exists('image'):
        os.makedirs('image')

    # val_accu = test(net, criterion, images_val, labels=labels_val, is_test=False)
    # print('val_accu = {}'.format(val_accu))
    if file_read_type:
        accuracy_list, validate_accuracy_list, loss_list = train(net, train_dataset_file, images_val_list, labels_val,
                                                                 batch_size, num_workers, criterion, optimizer,
                                                                 plot=True,
                                                                 plot_accuracy_name='image/accuracy_ResNet_{}.png'.format(
                                                                     run_name),
                                                                 plot_loss_name='image/loss_ResNet_{}.png'.format(
                                                                     run_name),
                                                                 plot_type='ResNet', save=True,
                                                                 save_name='./model/ResNet_paras_{}.pkl'.format(
                                                                     run_name), sampled=sampled, is_file_type=True,
                                                                 model_type='resnet')

    else:
        accuracy_list, validate_accuracy_list, loss_list = train(net, train_dataset, images_val, labels_val, batch_size,
                                                                 num_workers, criterion, optimizer,
                                                                 plot=True,
                                                                 plot_accuracy_name='image/accuracy_ResNet_{}.png'.format(
                                                                     run_name),
                                                                 plot_loss_name='image/loss_ResNet_{}.png'.format(
                                                                     run_name), plot_type='ResNet',
                                                                 save=True,
                                                                 save_name='./model/ResNet_paras_{}.pkl'.format(
                                                                     run_name))


    if not os.path.exists('tables'):
        os.makedirs('tables')

    file_name = 'ResNet_table_{}.pkl'.format(run_name)
    table_dict = {'num_workers': num_workers, 'train_accu': accuracy_list, 'val_accu': validate_accuracy_list,
                  'loss': loss_list}
    save_object(table_dict, os.path.join('tables', file_name))



def predict_with_best_net(run_name, sampled=False):
    path = 'model/ResNet_paras_{}.pkl'.format(run_name)
    net = my_ResNet(requeires_grad=False)
    if torch.cuda.is_available():
        net.load_state_dict(torch.load(path))
        net = net.cuda()
    else:
        net.load_state_dict(torch.load(path, map_location='cpu'))

    _, _, _, _, image_test_list, test_filenames = load_file_list(sampled=sampled)

    criterion = nn.CrossEntropyLoss()

    prediction = test(net, criterion, image_test_list, is_test=True, sampled=sampled, is_file_type=True,
                      model_type='resnet')

    prediction_dict = {}
    for i in range(len(test_filenames)):
        id = int(test_filenames[i].split('.', 1)[0])
        prediction_dict[id] = prediction[i]

    if not os.path.exists('result'):
        os.makedirs('result')

    file_out = open('./result/result_ResNet_{}.csv'.format(run_name), 'w')
    file_out.write('id,label\n')
    for key in sorted(prediction_dict.keys()):
        file_out.write('{},{}\n'.format(key, prediction_dict[key]))

    file_out.close()


if __name__ == '__main__':
    sampled = False
    run_name = 'lr0.0003'

    print('start to train')
    main(sampled=sampled, run_name=run_name)

    print('start to test')
    predict_with_best_net(run_name=run_name, sampled=sampled)
