import json
import time
from multiprocessing import Pool
from tqdm import tqdm

from notebook_features import get_ntb

def main():
    with open('ntbs_list.json', 'r') as fp:
        start, step = 5000, 1000
        ntb_list = json.load(fp)[start:start+step]

    with tqdm(total=len(ntb_list)) as pbar:
        with Pool(processes=6) as pool:
            for stats in pool.imap_unordered(get_ntb, ntb_list, 
                                             chunksize=1):
                pbar.update(1)

    print('Finishing...')


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
