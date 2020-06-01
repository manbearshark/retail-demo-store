import random
import datetime
import uuid
import json
import numpy as np
import pprint
from faker import Faker
from faker.providers import internet
from faker.providers import user_agent
from faker.providers import profile
from scipy.stats import truncnorm

# Setup Faker
fake = Faker()
fake.add_provider(internet)
fake.add_provider(user_agent)
fake.add_provider(profile)

# Normally distribute ages between 18 and 100 with a mean age of 32.
age_min = 18
age_max = 100
age_mean = 32
age_sd = 15

age_dist = truncnorm((age_min - age_mean) / age_sd, (age_max - age_mean) / age_sd, loc=age_mean, scale=age_sd)

class UserPool:
  def __init__(self, file):
    self.users = []
    self.active = []
    self.file = file
    with open(file) as f:
      data = json.load(f)
    for saved_user in data:
      user = User.from_file(saved_user)
      self.users.append(user)

  def size(self):
    return len(self.users) + len(self.active)

  def active_users(self):
    return len(self.active)

  def grow_pool(self, num_users):
    for i in range(num_users):
      self.users.append(User())
  
  def user(self, select_active=False):
    if len(self.users) == 0:
      self.grow_pool(1000)
      self.save(self.file)  # Cache the whole pool back to the file
    if select_active and len(self.active) > 0:
      user = random.choice(self.active)
    else:
      user = self.users.pop(random.randrange(len(self.users)))
      self.active.append(user)
    return user

  def save(self, file):
    all_users = []
    all_users.extend(self.users)
    all_users.extend(self.active)
    json_data = json.dumps(all_users, default=lambda x: x.__dict__)
    f = open(file, 'w')
    f.write(json_data)

class User:
  def __init__(self):
    self.id = random.randint(1000000000, 99999999999)
    self.gender = random.choice(['M', 'F'])
    if self.gender == 'F':
        self.first_name = fake.first_name_female()
        self.last_name = fake.last_name_female()
    else:
        self.first_name = fake.first_name_male()
        self.last_name = fake.last_name_male()

    address_state = fake.state_abbr(include_territories=True)
    email_first = self.first_name.replace(' ', '').lower()
    email_last = self.last_name.replace(' ', '').lower()
    self.email = f'{email_first}.{email_last}@example.com'
    self.age = int(age_dist.rvs())
    self.name = f'{self.first_name} {self.last_name}'
    self.username = f'user{self.id}'
    # These are hard-coded from the AWS samples Retail Demo Store workshop
    self.persona = random.choice(["apparel_housewares","footwear_outdoors","electronics_beauty","jewelry_accessories"])
    self.traits = {}

    ios_token = fake.ios_platform_token()
    ios_identifiers = ios_token.split(' ')
    android_token = fake.android_platform_token()
    android_identifiers = android_token.split(' ')

    self.platforms = {
      "ios": {
        "anonymous_id": str(uuid.uuid4()),
        "advertising_id": str(uuid.uuid4()),
        "user_agent": ios_token,
        "model": ios_identifiers[0],
        "version": ios_identifiers[4]
      },
      "android": {
        "anonymous_id": str(uuid.uuid4()),
        "advertising_id": str(uuid.uuid4()),
        "user_agent": android_token,
        "version": android_identifiers[1] 
      },
      "web": {
        "anonymous_id": str(uuid.uuid4()),
        "user_agent": fake.user_agent() 
      }
    }

    self.addresses = [
      {
        'first_name': self.first_name,
        'last_name': self.last_name,
        'address1': fake.street_address(),
        'address2': '',
        'country': 'US',
        'city': fake.city(),
        'state': address_state,
        'zipcode': fake.postcode_in_state(state_abbr=address_state),
        'default': True
      }
    ]
    
  def set_traits(self, traits):
    if traits != None:
      for (k,v) in traits.items():
        self.traits[k] = random.choice(v)
  
  def get_platform_data(self, platform):
    return self.platforms[platform]

  def toJson(self):
    return self.__repr__()

  def __repr__(self):
    return json.dumps(self.__dict__)

  @classmethod
  def from_file(cls, user_dict):
    user = cls()
    for (k,v) in user_dict.items():
      setattr(user,k, v)  # Danger, Will Robinson 
    return user