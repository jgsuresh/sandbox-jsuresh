import subprocess


# loop over all possibilities
# copy calib_template.py to the corresponding file, and change the corresponding things inside of it.
# (run separately?)

"""
# Key parameters:
catch_num = 0
calib_stage = 1
pop_version = 0
hs_version = 0
# nmf_version = 0
importation_version = 0
mode = "fast"
num_cores = 8
priority = "AboveNormal"
"""

burnins = False
mode = "full"
calib_stage = 2
num_cores = 2
priority = "AboveNormal"
NMF80 = True


template_fp = 'calib_template.py'

mozamb_catch_list = ["Chichuco","Chicutso","Magude-Sede-Facazissa","Mahel","Mapulanguene","Moine","Motaze","Panjane-Caputine"]


catch_num_list = [2] #list(range(4,8))#[1] #list(range(8))
pop_version_list = [0] #[0,1]
hs_version_list = [1] #[0,1]
importation_version_list = [1]

for catch_num in catch_num_list:
    catch = mozamb_catch_list[catch_num]

    for pop_version in pop_version_list:
        for hs_version in hs_version_list:
            for importation_version in importation_version_list:

                if burnins:
                    fn = "{}_pop{}_BURNIN.py".format(catch, pop_version)
                elif NMF80:
                    fn = "{}_pop{}_hs{}_imp{}_NMF80.py".format(catch, pop_version, hs_version, importation_version)
                else:
                    fn = "{}_pop{}_hs{}_imp{}.py".format(catch,pop_version,hs_version,importation_version)

                template = open(template_fp,'r')
                script = open(fn,'w')

                for t_line in template:
                    s_line = t_line.replace('catch_num = 1','catch_num = {}'.format(catch_num))
                    s_line = s_line.replace('calib_stage = 1','calib_stage = {}'.format(calib_stage))
                    s_line = s_line.replace('pop_version = 0', 'pop_version = {}'.format(pop_version))
                    s_line = s_line.replace('hs_version = 0','hs_version = {}'.format(hs_version))
                    s_line = s_line.replace('importation_version = 0','importation_version = {}'.format(importation_version))
                    s_line = s_line.replace('mode = \"fast\"','mode = \"{}\"'.format(mode))
                    s_line = s_line.replace('num_cores = 8','num_cores = {}'.format(num_cores))
                    s_line = s_line.replace('priority = \"AboveNormal\"', 'priority = \"{}\"'.format(priority))
                    if burnins:
                        s_line = s_line.replace('samples_per_iteration = 32', 'samples_per_iteration = 100')
                        s_line = s_line.replace('sim_runs_per_param_set = 4', 'sim_runs_per_param_set = 2')
                        s_line = s_line.replace('max_iterations = 10', 'max_iterations = 1')
                        s_line = s_line.replace('sigma_r=0.05', 'sigma_r=0.2')
                        s_line = s_line.replace("COMPS_calib_exp_name = \'Calib_{}_pop{}_hs{}_imp{}_stage{}\'.format(catch, pop_version, hs_version, importation_version, calib_stage)",
                                                "COMPS_calib_exp_name = \'Calib_{}_pop{}_burnin\'.format(catch, pop_version)",)
                    else:
                        s_line = s_line.replace('sim_runs_per_param_set = 4', 'sim_runs_per_param_set = 2')

                    if NMF80:
                        s_line = s_line.replace('from GriddedCalibSite import GriddedCalibSite', 'from GriddedCalibSite_NMF import GriddedCalibSite')
                        s_line = s_line.replace('HFCA_exp_name = \'Calib_{}_pop{}_hs{}_imp{}_HFCA\'.format(catch, pop_version, hs_version, importation_version, calib_stage)',
                                                'HFCA_exp_name = \'Calib_{}_pop{}_hs{}_imp{}_NMF80_HFCA\'.format(catch, pop_version, hs_version, importation_version, calib_stage)')

                    script.write(s_line)

                template.close()
                script.close()

                print("Executing {}".format(fn))
                subprocess.Popen(["python",fn])


