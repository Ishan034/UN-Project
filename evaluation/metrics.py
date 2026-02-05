import numpy as np

def hotspot_overlap(pred, actual, threshold=0.6):
    pred_hot = pred > threshold
    actual_hot = actual > threshold
    intersection = np.logical_and(pred_hot, actual_hot).sum()
    union = np.logical_or(pred_hot, actual_hot).sum()
    return intersection / (union + 1e-6)


def conflicts_prevented(pred_hotspots, conflict_zones):
    avoided = np.logical_and(pred_hotspots, ~conflict_zones)
    return avoided.sum()
