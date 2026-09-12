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
    def set_config(self, pop_size, gens, elites, extras, tournament, ord_mut, act_mut, cond_mut, dyn_k):
        self.POPULATION_SIZE = pop_size
        self.MAX_GENERATIONS = gens
        self.N_ELITE = elites
        self.EXTRA_STRATEGIES = extras
        self.TOURNAMENT_SIZE = tournament
        
        #MUTATION
        self.ORDER_MUTATION = ord_mut
        self.ACTION_MUTATION = act_mut
        self.CONDITION_MUTATION = cond_mut

        self.DYNAMIC_K = dyn_k

        if self.N_ELITE + self.EXTRA_STRATEGIES > self.POPULATION_SIZE:
            raise Exception("Invalid GA configuration: N_ELITES + EXTRA_STRATEGIES must be lower than POPULATION_SIZE")