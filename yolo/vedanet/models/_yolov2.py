import os
from collections import OrderedDict, Iterable
import torch
import torch.nn as nn
from .. import loss
from .yolo_abc import YoloABC
from ..network import backbone
from ..network import head

__all__ = ['Yolov2']


class Yolov2(YoloABC):
    def __init__(self, num_classes=20, weights_file=None, input_channels=3,
                 anchors = [(42.31,55.41), (102.17,128.30), (161.79,259.17), (303.08,154.90), (359.56,320.23)],
                 anchors_mask=[(0,1,2,3,4)], is_train=True, clear=False, test_args=None):
        """ Network initialisation """
        super().__init__()

        # Parameters
        self.num_classes = num_classes
        self.anchors = anchors
        self.anchors_mask = anchors_mask
        self.nloss = len(self.anchors_mask)
        self.is_train = is_train
        self.test_args = test_args

        self.loss = None
        self.postprocess = None

        self.backbone = backbone.Darknet19()
        self.head = head.Yolov2(num_anchors=len(anchors_mask[0]), num_classes=num_classes)

        if weights_file is not None:
            self.load_weights(weights_file, clear)
        else:
            self.init_weights(slope=0.1)

    def _forward(self, x):
        middle_feats = self.backbone(x)
        features = self.head(middle_feats)
        loss_fn = loss.RegionLoss
        
        self.compose(x, features, loss_fn)

        return features

    def modules_recurse(self, mod=None):
        """ This function will recursively loop over all module children.

        Args:
            mod (torch.nn.Module, optional): Module to loop over; Default **self**
        """
        if mod is None:
            mod = self

        for module in mod.children():
            if isinstance(module, (nn.ModuleList, nn.Sequential, backbone.Darknet19, head.Yolov2)):
                yield from self.modules_recurse(module)
            else:
                yield module
