import numpy as np

from dtk.interventions.itn_age_season import add_ITN_age_season
from jsuresh_helpers.comps import submit_experiment_to_comps
from jsuresh_helpers.dtk_tools_modfn_sweeps import modfn_sweep_over_seeds
from pareto_biting.interventions import add_simple_itn, add_simple_hs
from pareto_biting.reports import add_event_recorder_with_every_update, add_counter, add_node_demo_report
from pareto_biting.scenarios import biting_risk_scenario, flat_spline_ento, modfn_sweep_over_transmission_intensity
from pareto_biting.setup_sim import build_project_cb

from gridded_sims.run.build_cb import kariba_ento

###################
# Run description #
###################
# Test run

##################################
# Core malaria config parameters #
##################################

cb = build_project_cb()


##################################
# Run-specific config parameters #
##################################
# e.g. simulation duration, serialization, input files

sim_duration = 65*365
cb.set_param("Simulation_Duration", sim_duration)
# cb.set_param("Simulation_Duration", 30)
# cb.set_param("Serialization_Type", "TIMESTEP")
# cb.set_param("Serialization_Time_Steps", [50*365])
cb.set_param("Max_Individual_Infections", 3)


#################################################
# Campaign events that apply to ALL simulations #
#################################################
# add_standard_interventions(cb)
# kariba_ento(cb, f_sc=7.5, a_sc=8.2) #fiducial
# kariba_ento(cb, f_sc=7, a_sc=7.7) #low 1/26/21
# kariba_ento(cb, f_sc=8, a_sc=8.7) #high 1/26/21

# flat_spline_ento(cb, f_sc=7, a_sc=7.7) #~1 bite per day
flat_spline_ento(cb, f_sc=6.5, a_sc=7.2) #~1/3 bite per day.  low 1/28/21

# cb.set_param("Age_Initialization_Distribution_Type", "DISTRIBUTION_OFF") # make everyone adults for simplicity in looking at risk distribution
add_simple_hs(cb, 0.6, start_day=sim_duration-15*365)
add_simple_itn(cb, 0.6, start_day=sim_duration-5*365)

scenario_num = 0
biting_risk_scenario(cb, scenario_num)

#####################
# Experiment sweeps #
#####################


modlists = []

num_seeds = 25
modlist = modfn_sweep_over_seeds(num_seeds)
modlists.append(modlist)

# f_sc_array = np.arange(6.5,8.5,0.1)
f_sc_array = np.arange(6,7,0.05)
modlist = modfn_sweep_over_transmission_intensity(f_sc_array)
modlists.append(modlist)




####################
# Reports and logs #
####################
# add_event_recorder_with_every_update(cb)
# add_counter(cb)
# add_node_demo_report(cb)

###############################
# Submission/COMPs parameters #
###############################

if scenario_num == 0:
    comps_experiment_name = "uniform_biting"
elif scenario_num == 1:
    comps_experiment_name = "lognormal_biting_sigma_1.68"
elif scenario_num == 2:
    comps_experiment_name = "exponential_biting"
elif scenario_num == 3:
    comps_experiment_name = "gaussian_biting"
elif scenario_num == 4:
    comps_experiment_name = "lognormal_biting_sigma_1.2"
elif scenario_num == 5:
    comps_experiment_name = "lognormal_biting_sigma_1.6"

# comps_priority = "Highest"
# comps_coreset = "emod_32cores"
comps_priority = "Normal"
comps_coreset = "emod_abcd"

comps_experiment_name += "_elim_sweep"

##################
# Job submission #
##################

if __name__=="__main__":
    submit_experiment_to_comps(cb,
                               comps_experiment_name,
                               comps_priority,
                               comps_coreset,
                               modlists=modlists,
                               experiment_tags={"biting": comps_experiment_name}
                               )
