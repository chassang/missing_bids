import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


class AuctionData(object):
    def __init__(self, reference_file):
        self.df_bids = pd.read_csv(reference_file)
        self.df_auctions = None
        self._list_available_auctions = None
        # by convention demand outcomes are y = (D, Pm, Pp)
        self._demand_outcomes = \
            {0: (0, 0, 0), 1: (1, 0, 0), 2: (0, 1, 0), 3: (1, 0, 1)}
        self._enum_categories = None
        self._num_histories = None
        self.set_bid_data(self.df_bids)

    def set_bid_data(self, df_bids):
        self.df_bids = df_bids
        self.generate_auction_data()
        self.add_most_competitive()
        self.df_bids = self.df_bids.loc[
            ~ (df_bids.norm_bid.isnull() |
               self.df_bids.most_competitive.isnull())
        ]

    def generate_auction_data(self):
        """
        generates an auction-level dataframe from bid-level dataframe df
        includes second lowest bidder
        """

        list_auctions = list(set(self.df_bids.pid))
        list_auctions.sort()
        data = []
        for a in list_auctions:
            this_df = self.df_bids[self.df_bids.pid == a]
            bids = list(this_df.norm_bid.dropna())
            if len(bids) > 1:
                bids.sort()
                lowest = bids[0]
                second_lowest = bids[1]
                data.append(
                    [a, lowest, second_lowest])

        df_auctions = pd.DataFrame(
            data=data,
            columns=['pid', 'lowest', 'second_lowest']
        )
        df_auctions = df_auctions.set_index('pid')

        self.df_auctions = df_auctions
        self._list_available_auctions = set(self.df_auctions.index)

    def add_most_competitive(self):
        self.df_bids['most_competitive'] = 0
        self.df_bids['most_competitive'] = \
            self.df_bids[['pid', 'norm_bid']].apply(
                self._add_most_competitive, axis=1
            )

    def _add_most_competitive(self, x):
        u, v = x
        if u in self.list_available_auctions:
            low1 = self.df_auctions.ix[u].lowest
            low2 = self.df_auctions.ix[u].second_lowest
            if v == low1:
                return low2
            else:
                return low1
        else:
            return np.NaN

    @property
    def list_available_auctions(self):
        return self._list_available_auctions

    @staticmethod
    def _encode(x, y, z):
        return 1000 + 100. * x + 10. * y + 1. * z

    def compute_demand_moments(self, rho_p=.001, rho_m=.05):
        self.df_bids['sample_D'] = \
            1. * (self.df_bids.norm_bid < self.df_bids.most_competitive)
        bid_up = (1 + rho_p) * self.df_bids.norm_bid
        bid_down = (1 - rho_m) * self.df_bids.norm_bid

        self.df_bids['sample_Pp'] = \
            1. * (self.df_bids.most_competitive < bid_up) * (
                self.df_bids.norm_bid < self.df_bids.most_competitive)

        self.df_bids['sample_Pm'] = \
            1. * (self.df_bids.most_competitive >= bid_down) * (
                self.df_bids.norm_bid >= self.df_bids.most_competitive)

        self.df_bids['category'] = 0

        self.df_bids['category'] = self._encode(
            self.df_bids['sample_D'], self.df_bids['sample_Pm'],
            self.df_bids['sample_Pp']
        )

    def counterfactual_demand(self, rho_p, rho_m, num=500):
        assert (rho_p > 0) & (rho_m > 0)
        range_rho = zip(np.linspace(0, rho_m,  num=num),
                        np.linspace(0, rho_p, num=num))
        demand = []
        index = []
        for this_rho_m, this_rho_p in range_rho:
            index += [-this_rho_m, this_rho_p]
            self.compute_demand_moments(this_rho_p, this_rho_m)
            demand += [
                (self.df_bids.sample_D + self.df_bids.sample_Pm).mean(),
                (self.df_bids.sample_D - self.df_bids.sample_Pp).mean()
            ]
        return pd.DataFrame(data=demand,
                            index=index,
                            columns=['demand']).sort_index()

    def categorize_histories(self):
        ''' category = 1xyz with x, y, z = d, p_m, p_p'''
        self._enum_categories = {}
        for v in self.demand_outcomes.values():
            c = self._encode(*v)
            self.enum_categories[v] = np.sum(self.df_bids.category == c)

        self._num_histories = sum(self.enum_categories.values())

    def get_demand(self, p_c):
        """
        :param p_c: likelihood of conserving auctions in each category
        :return: sample tuple (D, Pm, Pp) corresponding to selection p_C
        """
        mean = np.array([0., 0., 0.])
        for i, z in enumerate(p_c):
            v = self.demand_outcomes[i]
            mean += z * np.array(v) * self.enum_categories[v] / float(
                self.num_histories)
        return tuple(mean)

    def get_competitive_share(self, p_c):
        c = 0
        for i, z in enumerate(p_c):
            v = self.demand_outcomes[i]
            c += z * self.enum_categories[v] / float(self._num_histories)
        return c

    @property
    def enum_categories(self):
        return self._enum_categories

    @property
    def num_histories(self):
        return self._num_histories

    @property
    def demand_outcomes(self):
        return self._demand_outcomes


def hist_plot(this_delta, title =''):
    sns.plt.figure(figsize=(10,6))
    sns.distplot(
        this_delta, kde=False,
        hist_kws=dict(alpha=1),
        bins=200,
        hist=True,
        norm_hist=1,
    )
    plt.title(title)
    sns.plt.tight_layout(), plt.show()