import numpy as np

# Simple placeholder grid alignment

def align_layers(image, layers):
    """
    Aligns auxiliary layers to satellite image grid.
    Assumes all inputs already roughly geo-aligned.
    """
    h, w = image.shape[-2:]
    aligned = []
    for layer in layers:
        aligned.append(layer[..., :h, :w])
    return np.stack(aligned, axis=1)
