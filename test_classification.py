import argparse
import torch
from utilities.utils import model_parameters, compute_flops
from utilities.train_eval_classification import validate
import os
from data_loader.classification.imagenet import val_loader as loader
#============================================
__author__ = "Sachin Mehta"
__license__ = "MIT"
__maintainer__ = "Sachin Mehta"
#============================================


def main(args):
    # create model
    if args.model == 'basic_dw':
        from model.classification import basic_dw as net
        model = net.CNNModel(args)
    elif args.model == 'basic_vw':
        from model.classification import basic_vw as net
        model = net.CNNModel(args)
    elif args.model == 'shuffle_dw':
        from model.classification import shufflenetv2 as net
        model = net.CNNModel(args)
    elif args.model == 'shuffle_vw':
        from model.classification import dicenet as net
        model = net.CNNModel(args)
    else:
        NotImplementedError('Model {} not yet implemented'.format(args.model))
        exit()

    num_params = model_parameters(model)
    flops = compute_flops(model)
    print('FLOPs: {:.2f} million'.format(flops))
    print('Network Parameters: {:.2f} million'.format(num_params))

    if not os.path.isfile(args.weights):
        print('Weight file does not exist at {}'.format(args.weights))
        exit(-1)

    num_gpus = torch.cuda.device_count()
    device = 'cuda' if num_gpus >=1 else 'cpu'
    weight_dict = torch.load(args.weights, map_location=torch.device(device))
    model.load_state_dict(weight_dict)

    if num_gpus >= 1:
        args.data_parallel = True
        model = torch.nn.DataParallel(model)
        model = model.cuda()
        if torch.backends.cudnn.is_available():
            import torch.backends.cudnn as cudnn
            cudnn.benchmark = True
            cudnn.deterministic = True

    # Data loading code
    val_loader = loader(args)
    validate(val_loader, model, device=device)


if __name__ == '__main__':
    model_names = ['basic_dw', 'basic_vw', 'shuffle_dw', 'shuffle_vw']

    parser = argparse.ArgumentParser(description='Testing efficient networks')
    parser.add_argument('--workers', default=4, type=int, help='number of data loading workers (default: 4)')
    parser.add_argument('--data', default='', help='path to dataset')
    parser.add_argument('--batch-size', default=512, type=int, help='mini-batch size (default: 256)')
    parser.add_argument('--num-classes', default=1000, type=int, help='# of classes in the dataset')
    parser.add_argument('--s', default=1, type=float, help='Factor by which output channels should be reduced (s > 1 for increasing the dims while < 1 for decreasing)')
    parser.add_argument('--weights', type=str, default='', help='weight file')
    parser.add_argument('--inpSize', default=224, type=int, help='Input size')
    ##Select a model
    parser.add_argument('--model', default='basic', choices=model_names, help='Which model? basic= basic CNN model, res=resnet style, shuffle=shufflenetv2 style)')
    parser.add_argument('--model-width', default=224, type=int, help='Model width')
    parser.add_argument('--model-height', default=224, type=int, help='Model height')
    parser.add_argument('--channels', default=3, type=int, help='Input channels')

    args = parser.parse_args()
    main(args)