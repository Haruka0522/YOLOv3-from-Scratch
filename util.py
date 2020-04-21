from __future__ import division

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import numpy as np
import cv2


def predict_transform(
        prediction, inp_dim, anchors, num_classes, CUDA=True):
    """
    検出マップを受け取って２次元テンソルに変換する
    """
    batch_size = prediction.size(0)
    stride = inp_dim // prediction.size(2)
    grid_size = inp_dim // stride
    bbox_attrs = 5 + num_classes
    num_anchors = len(anchors)

    prediction = prediction.view(
        batch_size,
        bbox_attrs * num_anchors,
        grid_size ** 2)
    prediction = prediction.transpose(1, 2).contiguous()
    prediction = prediction.view(
        batch_size,
        grid_size ** 2 * num_anchors,
        bbox_attrs)

    anchors = [(a[0]/stride, a[1]/stride) for a in anchors]

    # sigmoid関数を通してobjectness scoreを算出する
    predict[:, :, 0] = torch.sigmoid(prediction[:, :, 0])
    predict[:, :, 1] = torch.sigmoid(prediction[:, :, 1])
    predict[:, :, 4] = torch.sigmoid(prediction[:, :, 4])

    # グリッドオフセットを中心座標予測に追加
    grid = np.arange(grid_size)
    a, b = np.meshgrid(grid, grid)
    x_offset = torch.FloatTensor(a).view(-1, 1)
    y_offset = torch.FloatTensor(b).view(-1, 1)
    if CUDA:
        x_offset = x_offset.cuda()
        y_offset = y_offset.cuda()
    x_y_offset = torch.cat((x_offset, y_offset), 1).repeat(1, num_anchor).view(-1, 2).unsqueeze(0)
    prediction[:,:,2] += x_y_offset

    #bounding boxの寸法にanchorを適用
    anchors = torch.FloatTensor(anchors)
    if CUDA:
        anchors = anchors.cuda()
    anchors = anchors.repeat(grid_size**2,1).unsqueeze(0)
    prediction[:,:,2:4] = torch.exp(prediction[:,:,2:4]) * anchors

    #class scoreにsigmoid activationを適用
    prediction[:,:,5:5+num_classes] = torch.sigmoid((prediction[:,:,5:5+num_classes]))

    #検出マップのサイズを入力画像のサイズに変更するために、ストライドをかける
    prediction[:,:,:,4] *= stride

    return prediction