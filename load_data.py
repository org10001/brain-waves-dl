import numpy as np
import cfg
from sklearn import preprocessing


def filter_single_subset(data, filter_classes):
    """filter a subset from a npy file"""
    # data = np.load(filepath)
    data_l = len(data)
    idx = np.zeros((data_l,), dtype=bool)
    # the following two lines may not necessary
    ls1 = data[:, -1].flatten() + 0.5
    ls = ls1.astype(int)
    # ls = (data[:, -1].flatten()).astype(int)
    for filter_c in filter_classes:
        idx += (ls == filter_c)
    return data[idx]


def load_files(files, filter_classes, is_filter=True):
    """
    filter from a list of npy files, and return filtered data combined from the npy files
    return is list of np array, each np array contain samples and ls.
    """
    subsets = list()
    for f in files:
        subset = np.load(f)
        if is_filter:
            subset_filter = filter_single_subset(subset, filter_classes)
            subsets.append(subset_filter)
        else:
            subsets.append(subset)
    return subsets


def div_subset_samples_labels(subset):
    """
    3001d is 3000d + 1d, samples and labels
    :param data_set: 3001d, samples
    :return: samples, labels
    """
    labels1 = subset[:, -1] + 0.5
    labels = labels1.astype(int)
    return subset[:, :-1], labels


def div_subsets_samples_labels(subsets):
    samples_subs = list()
    ls_subs = list()
    for subset in subsets:
        samples_sub, ls_sub = div_subset_samples_labels(subset)
        samples_subs.append(samples_sub)
        ls_subs.append(ls_subs)
    return samples_subs, ls_subs


def convert_ls_1hot(ls, classes=cfg.classes):
    """convert 1d labels to 1hot labels"""
    ls_1hot = np.zeros((len(ls), len(classes)))
    for i, c in enumerate(classes):
        idx = (ls == c)
        ls_1hot[:, i][idx] = 1
    return ls_1hot


def convert_1hot_ls(one_hot, classes=cfg.classes):
    idx = np.argmax(one_hot, axis=1)
    np_classes = np.asarray(classes)
    return np_classes[idx]


def div_subset_samples_labels_1hot(sub_data_set, classes):
    """
    data_set is 3000d + 1d (data_set), samples + labels
    :return: 3000d samples, 1hot labels
    """
    samples, ls = div_subset_samples_labels(sub_data_set)
    ls_1hot = convert_ls_1hot(ls, classes)
    return samples, ls_1hot


def div_subsets_samples_labels_1hot(subsets, classes):
    samples_subs = list()
    ls_subs = list()
    for subset in subsets:
        samples_sub, ls_sub = div_subset_samples_labels_1hot(subset, classes)
        samples_subs.append(samples_sub)
        ls_subs.append(ls_subs)
    return samples_subs, ls_subs


def load_origin_data(files, classes, is_filter=True, is_1hot=True):
    """
    load data from specified files (files is a list)
    for example, load train samples and ls use `load_origin_data(config.train_fs, config.classes)`
    :return: ([sample_subsets, ls_subsets])
    """
    data_sets = load_files(files, classes, is_filter)
    if is_1hot:
        samples, ls = div_subsets_samples_labels_1hot(data_sets, classes)
    else:
        samples, ls = div_subsets_samples_labels(data_sets)
    return samples, ls


# fft
def convert_to_freq_domain(samples):
    m, n = samples.shape
    freq_samples_all = np.fft.fft(samples, n=n, axis=1)
    freq_samples = np.abs(freq_samples_all[:, :int(n / 2)])
    return freq_samples


def convert_subsets_to_freq_domain(samples_subs):
    freqs_list = list()
    for samples_sub in samples_subs:
        freqs = convert_to_freq_domain(samples_sub)
        freqs_list.append(freqs)
    return freqs_list


def norm_scale_respectively(samples_subs):
    norm_subs = list()
    for samples_sub in samples_subs:
        norm_sub = preprocessing.scale(samples_sub)
        norm_subs.append(norm_sub)
    return norm_subs


# normalization: standardize
def get_mu_sigma(train_samples):
    """
    get mu, sigma for standard normalization
    """
    mu = np.average(train_samples, axis=0)
    sigma = np.std(train_samples, axis=0)
    return mu, sigma


def standard_normalization(samples, mu, sigma):
    return (samples - mu) / sigma


# normalization: scale ( (x - min)/(max - min) )
def get_max_min(train_samples):
    max_v = np.max(train_samples, axis=0)
    min_v = np.min(train_samples, axis=0)
    return max_v, min_v


def scale_normalization(samples, max_v, min_v):
    return (samples - min_v) / (max_v - min_v)


# train set, vali set, test set
# usage:
# tvt = TrainValiTest()
# tvt.load()
# train_samples, train_ls  = tvt.train_samples_ls()
# vali_samples, vali_ls = tvt.vali_samples_ls()
# test_samples, test_ls = tvt.test_samples_ls()
class TrainValiTest:

    def __init__(self, is_fft=cfg.is_fft, norm_flag=cfg.norm_flag, train_fs=cfg.train_fs,
                 vali_fs=cfg.vali_fs, test_fs=cfg.test_fs, classes=cfg.classes, fft_clip=cfg.fft_clip):
        self.is_fft = is_fft
        self.norm_flag = norm_flag
        self.train_fs = train_fs
        self.vali_fs = vali_fs
        self.test_fs = test_fs
        self.classes = classes
        self.mu = None
        self.sigma = None
        self.max_v = None
        self.min_v = None
        self.train_samples = None
        self.train_ls = None
        self.vali_samples = None
        self.vali_ls = None
        self.test_samples = None
        self.test_ls = None
        self.raw_test_samples = None
        self.raw_test_ls = None
        self.fft_clip = fft_clip
        # self.load()

    def load(self):
        # origin
        train_samples, train_ls = load_origin_data(self.train_fs, self.classes)
        vali_samples, vali_ls = load_origin_data(self.vali_fs, self.classes)
        test_samples, test_ls = load_origin_data(self.test_fs, self.classes)
        raw_test_samples, raw_test_ls = load_origin_data(self.test_fs, self.classes,
                                                         is_filter=False, is_1hot=False)

        # fft
        if self.is_fft:
            train_samples = convert_subsets_to_freq_domain(train_samples)
            vali_samples = convert_to_freq_domain(vali_samples)
            test_samples = convert_to_freq_domain(test_samples)
            raw_test_samples = convert_to_freq_domain(raw_test_samples)
            if self.fft_clip > 0:
                train_samples = train_samples[:, :self.fft_clip]
                vali_samples = vali_samples[:, :self.fft_clip]
                test_samples = test_samples[:, :self.fft_clip]
                raw_test_samples = raw_test_samples[:, :self.fft_clip]

        # normalization
        if self.norm_flag == 1:
            self.mu, self.sigma = get_mu_sigma(train_samples)
            train_samples = standard_normalization(train_samples, self.mu, self.sigma)
            vali_samples = standard_normalization(vali_samples, self.mu, self.sigma)
            test_samples = standard_normalization(test_samples, self.mu, self.sigma)
            raw_test_samples = standard_normalization(raw_test_samples, self.mu, self.sigma)
        elif self.norm_flag == 2:
            self.max_v, self.min_v = get_max_min(train_samples)
            train_samples = scale_normalization(train_samples, self.max_v, self.min_v)
            vali_samples = scale_normalization(vali_samples, self.max_v, self.min_v)
            test_samples = scale_normalization(test_samples, self.max_v, self.min_v)
            raw_test_samples = scale_normalization(raw_test_samples, self.max_v, self.min_v)

        self.train_samples = train_samples
        self.train_ls = train_ls
        self.vali_samples = vali_samples
        self.vali_ls = vali_ls
        self.test_samples = test_samples
        self.test_ls = test_ls
        self.raw_test_samples = raw_test_samples
        self.raw_test_ls = raw_test_ls

    def train_samples_ls(self):
        return self.train_samples, self.train_ls

    def vali_samples_ls(self):
        return self.vali_samples, self.vali_ls

    def test_samples_ls(self):
        return self.test_samples, self.test_ls

    def raw_test_samples_ls(self):
        return self.raw_test_samples, self.raw_test_ls