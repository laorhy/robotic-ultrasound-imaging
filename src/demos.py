import numpy as np
import glfw

import robosuite as suite
from robosuite.models import MujocoWorldBase
from robosuite.models.arenas import EmptyArena
from robosuite.utils.mjcf_utils import new_joint, array_to_string
from robosuite.wrappers import GymWrapper
from robosuite import load_controller_config

from mujoco_py import MjSim, MjViewer

from my_models.objects import SoftTorsoObject, BoxObject
from helper import relative2absolute_joint_pos_commands, set_initial_robot_state, \
    transform_ee_frame_axes, create_mjsim_and_viewer, print_world_xml_and_soft_torso_params, \
    capture_image_frame


def controller_demo(experiment_name, save_data=False):
    
    env = suite.make(
            'Ultrasound',
            robots='UR5e',
            controller_configs=None,
            gripper_types=None,
            has_renderer = True,
            has_offscreen_renderer= False,
            use_camera_obs=False,
            use_object_obs=False,
            control_freq = 50,
            render_camera = 'sideview',
            horizon=1600    
        )

    # Reset the env
    env.reset()

    sim_time = env.horizon

    robot = env.robots[0]
    joint_pos_obs = np.empty(shape=(sim_time, robot.dof))
    ref_values = np.array([np.pi/2, 3*np.pi/2, -np.pi/4])

    goal_joint_pos = [ref_values[0], 0, 0, 0, 0, 0]
    kp = 2
    kd = 1.2

    for t in range(sim_time):
        if env.done:
            break
        env.render()
        
        action = relative2absolute_joint_pos_commands(goal_joint_pos, robot, kp, kd)

        if t > 1200:
            action = relative2absolute_joint_pos_commands([0, ref_values[2], 0, 0, 0, 0], robot, kp, kd)
        elif t > 800:
            action = relative2absolute_joint_pos_commands([0, 0, 0, 0, 0, 0], robot, kp, kd)
        elif t > 350:
            action = relative2absolute_joint_pos_commands([ref_values[1], 0, 0, 0, 0, 0], robot, kp, kd)

        observation, reward, done, info = env.step(action)
        joint_pos_obs[t] = np.arccos(observation['robot0_joint_pos_cos'])

    # close window
    env.close() 

    if save_data:
        np.savetxt('data/'+experiment_name+'_joint_pos_controller_test.csv', joint_pos_obs, delimiter=",")
        np.savetxt('data/'+experiment_name+'_ref_values_controller_test.csv', ref_values, delimiter=",")


def contact_btw_probe_and_body_demo(episodes, experiment_name, save_data=False):
    
    for episode in range(episodes):
        env = suite.make(
            'Ultrasound',
            robots='UR5e',
            controller_configs=None,
            gripper_types='UltrasoundProbeGripper',
            has_renderer = True,
            has_offscreen_renderer= False,
            use_camera_obs=False,
            use_object_obs=False,
            control_freq = 50,
            render_camera = None,
            horizon=700      
        )
    
        # Reset the env
        env.reset() 

        h = 0.01    # Timestep (default value from MuJoCo)

        sim_time = env.horizon
        robot = env.robots[0]
        num_robot_joints = robot.dof - 1 if robot.gripper.dof > 0 else robot.dof

        joint_torques = np.empty(shape=(sim_time, num_robot_joints))
        ee_forces = np.empty(shape=(sim_time, 3))
        ee_torques = np.empty(shape=(sim_time, 3))
        gripper_pos = np.empty(shape=(sim_time, 3))
        contact = np.empty(shape=(sim_time, 1))
        time = np.empty(shape=(sim_time, 1))

        goal_joint_pos = [0, -np.pi/4, np.pi/3, -np.pi/2, -np.pi/2, 0]
        goal_joint_pos = goal_joint_pos + [0] if robot.gripper.dof > 0 else goal_joint_pos
        kp = 2
        kd = 1.2

        for t in range(sim_time):
            if env.done:
                break
            env.render()
            
            action = relative2absolute_joint_pos_commands(goal_joint_pos, robot, kp, kd)

            if t > 400:
                goal_joint_pos = [0, -np.pi/4, np.pi, -np.pi/2, -np.pi/2, 0]
                goal_joint_pos = goal_joint_pos + [0] if robot.gripper.dof > 0 else goal_joint_pos

                action = relative2absolute_joint_pos_commands(goal_joint_pos, robot, kp, kd)

            observation, reward, done, info = env.step(action)

            joint_torques[t] = robot.torques 
            gripper_pos[t] = observation['robot0_eef_pos']
            time[t] = t*h
            ee_forces[t] = transform_ee_frame_axes(robot.ee_force) if robot.gripper_type == 'UltrasoundProbeGripper' else robot.ee_force
            ee_torques[t] = transform_ee_frame_axes(robot.ee_torque) if robot.gripper_type == 'UltrasoundProbeGripper' else robot.ee_torque
            if robot.has_gripper:
                contact[t] = observation['contact']

        if save_data:
            np.savetxt('data/'+experiment_name+str(episode)+'_joint_torques_contact_btw_probe_and_body.csv', joint_torques, delimiter=",")
            np.savetxt('data/'+experiment_name+str(episode)+'_time_contact_btw_probe_and_body.csv', time, delimiter=",")
            np.savetxt('data/'+experiment_name+str(episode)+'_ee_forces_contact_btw_probe_and_body.csv', ee_forces, delimiter=",")
            np.savetxt('data/'+experiment_name+str(episode)+'_ee_torques_contact_btw_probe_and_body.csv', ee_torques, delimiter=",")
            np.savetxt('data/'+experiment_name+str(episode)+'_contact_contact_btw_probe_and_body.csv', contact, delimiter=",")
            np.savetxt('data/'+experiment_name+str(episode)+'_gripper_pos_contact_btw_probe_and_body.csv', gripper_pos, delimiter=",")

        # close window
        env.close() 


def standard_mujoco_py_demo():

    env = suite.make(
            'Ultrasound',
            robots='Panda',
            controller_configs=None,
            gripper_types='UltrasoundProbeGripper',
            has_renderer = True,
            has_offscreen_renderer= False,
            use_camera_obs=False,
            use_object_obs=False,
            control_freq = 50,
            render_camera = None,
            horizon=1500      
        )

    sim, viewer = create_mjsim_and_viewer(env)

    for _ in range(env.horizon):
        sim.step()
        viewer.render()
        

def change_parameters_of_soft_body_demo(episodes):
 
    for _ in range(episodes):

        env = suite.make(
            'Ultrasound',
            robots='UR5e',
            controller_configs=None,
            gripper_types='UltrasoundProbeGripper',
            has_renderer = True,
            has_offscreen_renderer= False,
            use_camera_obs=False,
            use_object_obs=False,
            control_freq = 50,
            render_camera = None,
            horizon=800      
        )
        env.reset()

        print_world_xml_and_soft_torso_params(env.model)

        sim, viewer = create_mjsim_and_viewer(env)
    
        for _ in range(env.horizon):
            sim.step()
            viewer.render()
        
        glfw.destroy_window(viewer.window)



def gather_calibration_measurements():
    
    env = suite.make(
        'Ultrasound',
        robots='Panda',
        controller_configs=load_controller_config(default_controller = 'OSC_POSE'),
        gripper_types='UltrasoundProbeGripper',
        has_renderer = True,
        has_offscreen_renderer= False,
        use_camera_obs=False,   
        use_object_obs=False,
        control_freq = 100,
        render_camera = None,
        horizon=250,
        initialization_noise = None,
    )

    # Reset the env
    env.reset() 

    robot = env.robots[0]

    ee_z_force = np.empty(shape=(env.horizon, 1))
    ee_z_pos = np.empty(shape=(env.horizon, 1))
    ee_z_vel = np.empty(shape=(env.horizon, 1))

    for t in range(env.horizon):
        print(t)
        if env.done:
            break
        env.render()

        action = [0.2, 0.05, -0.2, 0, 0, 0]

        if t > 50:
            action = [0, 0, 0, 0, 0, 0]
        if t > 75:
            action = [0, 0, -0.4, 0, 0, 0]
        if t > 200:
            action = [0, 0, 0.8, 0, 0, 0]
        if t > 225:
            action = [0, 0, 0, 0, 0, 0]

        observation, reward, done, info = env.step(action)

        ee_z_force[t] = transform_ee_frame_axes(robot.ee_force)[-1] if robot.gripper_type == 'UltrasoundProbeGripper' else robot.ee_force[-1]
        ee_z_pos[t] = observation['robot0_eef_pos'][-1]
        ee_z_vel[t] = observation['gripper_velp'][-1]

    np.savetxt('data/calibration_z_force.csv', ee_z_force, delimiter=",")
    np.savetxt('data/calibration_z_pos.csv', ee_z_pos, delimiter=",")
    np.savetxt('data/calibration_z_vel.csv', ee_z_vel, delimiter=",")
   
    # close window
    env.close() 