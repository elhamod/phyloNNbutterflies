import matplotlib.pylab as plt
import os
import torch
import numpy as np

class model_activations(torch.nn.Module):
    def __init__(self, model, layer_name, dataset):
        super(model_activations, self).__init__()

        self.model = model
        self.dataset = dataset
        self.layer_name = layer_name

    def forward(self, x):
        if torch.cuda.is_available():
            x = x.to('cuda')
            
        if self.layer_name == 'coarse':
            return self.model.get_coarse(x, self.dataset)
        else:
            activations = self.model.activations
            return activations(x)[self.layer_name]
    
# Define the function for plotting the activations
def plot_activations(model, layer_name, input_img, experimentName, params, dataset, fileName="", n_splits=1, topA=5):
    if torch.cuda.is_available():
        input_img = input_img.to('cuda')
    
    activation = model_activations(model, layer_name, dataset)
    A = activation(input_img)
    if (layer_name == "coarse" or layer_name == "fine"):
        A = torch.nn.Softmax(dim=1)(A)
    print("Number of activations: ", A.shape)
    
    A = A.squeeze(0).detach().cpu().numpy()
    A_min = A.min().item()
    A_max = A.max().item()

    if topA is not None:
        A_topIndices = sorted(range(len(A)), key=lambda i: A[i], reverse=True)[:topA]
        A = A[A_topIndices]
    
    A_split = np.array_split(A, n_splits)

    thresh = A.max() / 1.5
    _, axes = plt.subplots(n_splits, 1, figsize=(25, 1.5*n_splits), dpi= 300)
    idx = 0
    for j, A_single in enumerate(A_split):
        ax = axes[j] if n_splits >1 else axes
        A_single = np.expand_dims(A_single, axis=0)
        feature_num = A_single.shape[1]
        
        # Set ticks
        if (layer_name == "coarse" or layer_name == "fine"):
            if layer_name == "fine":
                target_names = dataset.csv_processor.getFineList()
            else:
                target_names = dataset.csv_processor.getCoarseList()
            target_names =list(map(lambda x: x[1] + " - " + str(x[0]), enumerate(target_names))) 
            tick_marks = np.arange(len(target_names))
            ax.set_xticks(tick_marks)
            ax.set_xticklabels([target_names[i] for i in A_topIndices], rotation=45, ha='right')
        
        ax.imshow(A_single, vmin=A_min, vmax=A_max, cmap='Blues', extent=[idx-0.5, idx+feature_num-0.5, -0.5, 0.5])
        for i in range(feature_num):
            ax.text(i+idx, 0, "{:0.2f}".format(A_single[0, i]),
                     horizontalalignment="center",
                     color="white" if A[i] > thresh else "black")
        ax.set_xlim(idx-0.5, idx + feature_num-0.5)
        idx = idx + feature_num

   
    ax = plt.gca()
    ax.axes.yaxis.set_visible(False)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(os.path.join(experimentName, fileName+"_activations.pdf"), bbox_inches = 'tight',
    pad_inches = 0)
    # plt.suptitle("Activations - "+title, fontsize=10)
    plt.show()
    return A
