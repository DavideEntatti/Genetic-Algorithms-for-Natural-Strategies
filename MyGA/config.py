#Parametri algoritmo genetico
class config:
    #GENERAZIONE
    POPULATION_SIZE = 50
    MAX_GENERATIONS = 50
    N_ELITE = 5
    EXTRA_STRATEGIES = 5
    TOURNAMENT_SIZE = 8
    
    #MUTATION
    ORDER_MUTATION = 0.3
    ACTION_MUTATION = 0.2
    CONDITION_MUTATION = 0.3

    DYNAMIC_K = 0

    @classmethod
    def set_config(self, pop_size=None, gens=None, elites=None, extras=None,
                    tournament=None, ord_mut=None, act_mut=None, cond_mut=None, dyn_k=None):
        
        if pop_size is not None: self.POPULATION_SIZE = pop_size
        if gens is not None: self.MAX_GENERATIONS = gens
        if elites is not None: self.N_ELITE = elites
        if extras is not None: self.EXTRA_STRATEGIES = extras
        if tournament is not None: self.TOURNAMENT_SIZE = tournament
        
        #MUTATION
        if ord_mut is not None: self.ORDER_MUTATION = ord_mut
        if act_mut is not None: self.ACTION_MUTATION = act_mut
        if cond_mut is not None: self.CONDITION_MUTATION = cond_mut

        if dyn_k is not None: self.DYNAMIC_K = dyn_k

        if self.N_ELITE + self.EXTRA_STRATEGIES > self.POPULATION_SIZE:
            raise Exception("Invalid GA configuration: N_ELITES + EXTRA_STRATEGIES must be lower than POPULATION_SIZE")