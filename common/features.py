import minigrid
from minigrid.wrappers import ImgObsWrapper
from stable_baselines3 import PPO

from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
import gymnasium as gym
import torch
import torch.nn as nn

from stable_baselines3.sac import CnnPolicy, MlpPolicy, MultiInputPolicy


class CNNMinigridFeaturesExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space: gym.Space, features_dim: int = 512, normalized_image: bool = False) -> None:
        super().__init__(observation_space, features_dim)
        n_input_channels = observation_space.shape[0]
        self.cnn = nn.Sequential(
                nn.Conv2d(n_input_channels, 16, (2, 2)),
                nn.ReLU(),
                nn.Conv2d(16, 32, (2, 2)),
                nn.ReLU(),
                nn.Conv2d(32, 64, (2, 2)),
                nn.ReLU(),
                nn.Flatten(),
        )

        # # Compute shape by doing one forward pass
        with torch.no_grad():
            n_flatten = self.cnn(torch.as_tensor(observation_space.sample()[None]).float()).shape[1]

        self.linear = nn.Sequential(nn.Linear(in_features=n_flatten, out_features=features_dim), nn.ReLU())

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.linear(self.cnn(observations))


class CompositeFeaturesExtractor(BaseFeaturesExtractor):
    """组合节点用到的特征提取器"""

    def __init__(self, observation_space: gym.Space, features_dim: int = 512, normalized_image: bool = False) -> None:
        super().__init__(observation_space, features_dim)
        n_input_channels = observation_space['image'].shape[0]
        self.cnn = nn.Sequential(
                nn.Conv2d(n_input_channels, 16, (2, 2)),
                nn.ReLU(),
                nn.Conv2d(16, 32, (2, 2)),
                nn.ReLU(),
                nn.Conv2d(32, 64, (2, 2)),
                nn.ReLU(),
                nn.Flatten(),
        )

        # # Compute shape by doing one forward pass
        with torch.no_grad():
            n_flatten = self.cnn(torch.as_tensor(observation_space['image'].sample()[None]).float()).shape[1]

        self.linear = nn.Sequential(
                nn.Linear(in_features=n_flatten + observation_space['status'].sample().shape[0] * 4,
                          out_features=features_dim),
                nn.ReLU())

    def forward(self, observations) -> torch.Tensor:
        features = self.cnn(observations['image'])
        status = observations['status']
        return self.linear(torch.cat((status, features), dim=1))
