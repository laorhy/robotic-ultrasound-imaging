import numpy as np

from mujoco_py import MjSim, MjViewer

from robosuite.models import MujocoWorldBase
from robosuite.models.arenas import EmptyArena
from robosuite.utils.mjcf_utils import new_joint

from my_models.objects import SoftTorsoObject, BoxObject
from helper import relative2absolute_joint_pos_commands, set_initial_state


def robosuite_simulation_controller_test(env, sim_time):
    # Reset the env
    env.reset()

    robot = env.robots[0]
    goal_joint_pos = [np.pi / 2, 0, 0, 0, 0, 0]
    kp = 2
    kd = 1.2

    for t in range(sim_time):
        if env.done:
            break
        env.render()
        
        action = relative2absolute_joint_pos_commands(goal_joint_pos, robot, kp, kd)

        if t > 1200:
            action = relative2absolute_joint_pos_commands([0, -np.pi/4, 0, 0, 0, 0], robot, kp, kd)
        elif t > 800:
            action = relative2absolute_joint_pos_commands([0, 0, 0, 0, 0, 0], robot, kp, kd)
        elif t > 400:
            action = relative2absolute_joint_pos_commands([3*np.pi/2, 0, 0, 0, 0, 0], robot, kp, kd)

        observation, reward, done, info = env.step(action)

    # close window
    env.close() 


def mujoco_py_simulation(env, sim_time):
    world = env.model 
    model = world.get_model(mode="mujoco_py")

    sim = MjSim(model)
    set_initial_state(sim, sim.get_state(), env.robots[0])
    viewer = MjViewer(sim)

    for _ in range(sim_time):
        sim.step()
        viewer.render()


def body_softness_test():
    world = MujocoWorldBase()
    arena = EmptyArena()
    arena.set_origin([0, 0, 0])
    world.merge(arena)

    soft_torso = SoftTorsoObject()
    obj = soft_torso.get_collision()

    box = BoxObject()
    box_obj = box.get_collision()

    obj.append(new_joint(name='soft_torso_free_joint', type='free'))
    box_obj.append(new_joint(name='box_free_joint', type='free'))

    world.merge_asset(soft_torso)

    world.worldbody.append(obj)
    world.worldbody.append(box_obj)
    model = world.get_model(mode="mujoco_py")

    sim = MjSim(model)
    viewer = MjViewer(sim)


    for _ in range(10000):
        sim.step()
        viewer.render()