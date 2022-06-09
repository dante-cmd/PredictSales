import numpy as np
from itertools import combinations, product
import pandas as pd, re

class Basket:
    
    def __init__(self, df:pd.DataFrame):
        """
        Columns of data frame must be binary values. I = 0 or 1
        Rows must be an id id some customer
        """
        self.X = df.values
        self.columns = df.columns.astype(str).values
        self.X_dumm = self.X == 1
    
    def UniSupport(self, t=0):
        """ 
        This compute the support of itemset I, where length is 1, |I|=1 
        """
        self.uni_t = t
        X_support = self.X_dumm.mean(axis=0)
        self.condition = X_support>t
        self.X_support_serie = pd.Series(X_support[self.condition],self.columns[self.condition] , name = 'UniSupport',)
        X_support_serie_export = self.X_support_serie.copy()
        X_support_serie_export.index = X_support_serie_export.index.str.replace(r'((?:.|\s)+)', r'T(\1)', regex=True)

        return X_support_serie_export #.sort_values(ascending=False)
    
    def PairSupport(self, t):
        """ 
        This compute the support of itemset I, where length is 2, |I|=2,
        given the min support above specified
        """
        self.pair_t = t
        feat_indx = np.where(self.condition)[0]
        support_pair_select = {}

        for comb in combinations(feat_indx, 2):
            X_support_select = self.X_dumm[:, comb].all(axis = 1).mean()
            columns_select = self.columns[np.asarray(comb)]
            if X_support_select > t:
                support_pair_select[tuple(columns_select)] = X_support_select
        self.support_pair_select_serie = pd.Series(support_pair_select, name='PairSupport')
        support_pair_select_serie_export = self.support_pair_select_serie.copy()
        support_pair_select_serie_export.index = ['T('+','.join(x) +')' for x in  support_pair_select_serie_export.index]
        support_pair_select_serie_export.index.name = 'T(A,B)'
        
        return support_pair_select_serie_export #.sort_values(ascending=False)

    def Confidence(self, given_set = 'A'):
        
        self.given_set = given_set
        df_support_uni = self.X_support_serie.reset_index().copy()
        df_support_uni.rename(columns={'index':f'{self.given_set}', 'UniSupport':f'UniSupport_{self.given_set}'}, inplace=True)
        df_support_uni[f'T({self.given_set})'] = self.UniSupport(self.uni_t).index
        
        self.support_pair_select_serie.index = self.support_pair_select_serie.index.set_names(['A', 'B'])
        df_support_pair = self.support_pair_select_serie.reset_index()
        df_support_pair['T(A,B)'] = self.PairSupport(self.pair_t).index

        df_support_total = df_support_pair.merge(df_support_uni, on=f'{self.given_set}')
        df_support_total[f'T(A,B)/T({self.given_set})'] = df_support_total['T(A,B)'].add('/' + df_support_total[f'T({self.given_set})'])
        df_support_total.set_index(f'T(A,B)/T({self.given_set})', inplace=True)
        df_support_total['Confidence'] = df_support_total['PairSupport']/df_support_total[f'UniSupport_{self.given_set}']
        self.df_support_total = df_support_total
        
        return  df_support_total['Confidence']#.sort_values(ascending=False)

    def Lift(self):
        lift_set = 'B' if self.given_set == 'A' else 'A'
        
        df_support_uni = self.X_support_serie.reset_index().copy()
        df_support_uni.rename(columns={'index':f'{lift_set}', 'UniSupport':f'UniSupport_{lift_set}'}, inplace=True)
        df_support_uni[f'T({lift_set})'] = self.UniSupport(self.uni_t).index

        df_support_total_lift = self.df_support_total.merge(df_support_uni, on = f'{lift_set}', how='left')
        df_support_total_lift['Lift'] = df_support_total_lift['Confidence']/df_support_total_lift[f'UniSupport_{lift_set}']
        df_support_total_lift.index = (
            df_support_total_lift["T(A,B)"] + "/" + df_support_total_lift[f"T({self.given_set})"] + df_support_total_lift[f"T({lift_set})"])
        df_support_total_lift.index.name = f"T(A,B)/T({self.given_set})T({lift_set})"

        return  df_support_total_lift['Lift']#.sort_values(ascending=False)