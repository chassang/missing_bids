from scripts.figures_import_helper import *
# %matplotlib inline

# before/after industry comparisons, using national data
print('='*20, '\n city level all')

# +
filename = 'tsuchiura_data.csv'
tsuchiura_data = asymptotics.AsymptoticAuctionData(
    os.path.join(path_data, filename))
tsuchiura_data = asymptotics.AsymptoticAuctionData(
    tsuchiura_data.df_bids.loc[tsuchiura_data.data.minprice.isnull()])

filename = 'municipal_pub_reserve_no_pricefloor.csv'
other_data = asymptotics.AsymptoticAuctionData(
    os.path.join(path_data, filename))

# +
s1 = set(other_data.df_bids.pid)
s2 = set(tsuchiura_data.df_bids.pid)

assert len(s2.intersection(s1)) == 0
# -

all_bids = pd.concat((other_data.df_bids, tsuchiura_data.df_bids), axis=0)
data = asymptotics.AsymptoticAuctionData.from_clean_bids(all_bids)

list_devs = [up_deviations, down_deviations, all_deviations]

list_solutions = []
for devs in list_devs:
    solutions, ties = compute_asymptotic_solution(
        data, devs)
    list_solutions.append(1 - ties - solutions * (1-ties))

print('saving plot\n')
pretty_plot(
    'city auctions',
    list_solutions,
    [r"deviations {}".format(dev_repr(devs)) for devs in list_devs],
    xlabel='minimum markup',
    mark=np.array(['k.:', 'k.--', 'k.-']),
    xticks=r3_min_markups
)

print('saving data\n')
save2frame(list_solutions,
           ['min_m={}'.format(m) for m in r3_min_markups],
           'city_auctions')


# varying maximum markup

list_max_markups = [.5, 1, 1.5]
devs = all_deviations
list_solutions = []

for max_markup in list_max_markups:
    markups = list(product(r3_min_markups, [max_markup]))
    this_solver = ComputeMinimizationSolution(
        solver_cls=asymptotics.ParallelAsymptoticSolver,
        metric=analytics.EfficientIsNonCompetitive,
        markups=markups
    )
    solutions, ties = this_solver(data, devs)
    list_solutions.append(1 - ties - solutions * (1-ties))

print('saving plot\n')
pretty_plot(
    'city auctions -- varying max markup',
    list_solutions,
    [r"max markup {}".format(max_markup) for max_markup in list_max_markups],
    xlabel='minimum markup',
    mark=np.array(['k.:', 'k.--', 'k.-']),
    xticks=r3_min_markups
)

print('saving data\n')
save2frame(list_solutions,
           ['min_m={}'.format(m) for m in r3_min_markups],
           'city_auctions_max_markup')
