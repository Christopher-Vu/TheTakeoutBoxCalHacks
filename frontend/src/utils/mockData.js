// Mock Data Generators for SafeRoute Application

// Mock Incidents
export const mockIncidents = [
  {
    id: 1,
    type: 'theft',
    description: 'Bike stolen from rack near coffee shop. Lock was cut through.',
    location: '2nd St & Market Ave',
    dateTime: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    imageUrl: null,
    coordinates: { lat: 37.7749, lng: -122.4194 }
  },
  {
    id: 2,
    type: 'assault',
    description: 'Verbal harassment reported near the park entrance after dark.',
    location: 'Central Park West Entrance',
    dateTime: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5 hours ago
    imageUrl: null,
    coordinates: { lat: 37.7739, lng: -122.4184 }
  },
  {
    id: 3,
    type: 'vandalism',
    description: 'Graffiti and broken glass found at bus stop.',
    location: 'Oak St Bus Stop #42',
    dateTime: new Date(Date.now() - 12 * 60 * 60 * 1000), // 12 hours ago
    imageUrl: null,
    coordinates: { lat: 37.7759, lng: -122.4204 }
  },
  {
    id: 4,
    type: 'harassment',
    description: 'Unwanted following reported for several blocks. Person felt unsafe.',
    location: 'Main St between 5th and 8th',
    dateTime: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
    imageUrl: null,
    coordinates: { lat: 37.7729, lng: -122.4174 }
  },
  {
    id: 5,
    type: 'theft',
    description: 'Package stolen from front porch during afternoon.',
    location: '456 Elm Street',
    dateTime: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
    imageUrl: null,
    coordinates: { lat: 37.7769, lng: -122.4214 }
  },
  {
    id: 6,
    type: 'other',
    description: 'Suspicious activity - person checking car door handles in parking lot.',
    location: 'Downtown Parking Garage Level 3',
    dateTime: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
    imageUrl: null,
    coordinates: { lat: 37.7779, lng: -122.4224 }
  },
  {
    id: 7,
    type: 'assault',
    description: 'Physical altercation witnessed outside bar area late night.',
    location: 'Broadway & 12th St',
    dateTime: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
    imageUrl: null,
    coordinates: { lat: 37.7719, lng: -122.4164 }
  },
  {
    id: 8,
    type: 'vandalism',
    description: 'Car window smashed, items stolen from vehicle.',
    location: 'Pine St near Shopping Center',
    dateTime: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
    imageUrl: null,
    coordinates: { lat: 37.7789, lng: -122.4234 }
  },
  {
    id: 9,
    type: 'theft',
    description: 'Wallet pickpocketed on crowded train during rush hour.',
    location: 'Transit Station - Red Line',
    dateTime: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
    imageUrl: null,
    coordinates: { lat: 37.7709, lng: -122.4154 }
  },
  {
    id: 10,
    type: 'harassment',
    description: 'Aggressive panhandling making people uncomfortable.',
    location: '1st Ave & Cherry St',
    dateTime: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000), // 4 days ago
    imageUrl: null,
    coordinates: { lat: 37.7799, lng: -122.4244 }
  },
  {
    id: 11,
    type: 'other',
    description: 'Poorly lit area with no security cameras. Reported feeling unsafe.',
    location: 'Underpass near River Trail',
    dateTime: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
    imageUrl: null,
    coordinates: { lat: 37.7699, lng: -122.4144 }
  },
  {
    id: 12,
    type: 'theft',
    description: 'Phone snatched while sitting at outdoor cafe.',
    location: 'Cafe District - Union Square',
    dateTime: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
    imageUrl: null,
    coordinates: { lat: 37.7809, lng: -122.4254 }
  },
  {
    id: 13,
    type: 'vandalism',
    description: 'Multiple mailboxes damaged and opened.',
    location: 'Residential Area - Maple Drive',
    dateTime: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000), // 6 days ago
    imageUrl: null,
    coordinates: { lat: 37.7689, lng: -122.4134 }
  },
  {
    id: 14,
    type: 'assault',
    description: 'Person threatened with weapon during attempted robbery.',
    location: 'ATM on Washington Blvd',
    dateTime: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 1 week ago
    imageUrl: null,
    coordinates: { lat: 37.7819, lng: -122.4264 }
  },
  {
    id: 15,
    type: 'harassment',
    description: 'Catcalling and inappropriate comments made to pedestrians.',
    location: 'Shopping District - 4th Ave',
    dateTime: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 1 week ago
    imageUrl: null,
    coordinates: { lat: 37.7679, lng: -122.4124 }
  }
];

// Helper function to format time ago
export const getTimeAgo = (date) => {
  const seconds = Math.floor((new Date() - date) / 1000);

  let interval = Math.floor(seconds / 31536000);
  if (interval >= 1) return interval + (interval === 1 ? ' year ago' : ' years ago');

  interval = Math.floor(seconds / 2592000);
  if (interval >= 1) return interval + (interval === 1 ? ' month ago' : ' months ago');

  interval = Math.floor(seconds / 86400);
  if (interval >= 1) return interval + (interval === 1 ? ' day ago' : ' days ago');

  interval = Math.floor(seconds / 3600);
  if (interval >= 1) return interval + (interval === 1 ? ' hour ago' : ' hours ago');

  interval = Math.floor(seconds / 60);
  if (interval >= 1) return interval + (interval === 1 ? ' minute ago' : ' minutes ago');

  return 'Just now';
};

// Mock Routes
export const generateMockRoutes = (origin, destination, mode) => {
  const routes = [
    {
      id: 1,
      duration: '12 min',
      durationMinutes: 12,
      distance: '0.8 mi',
      mode: mode || 'walking',
      safetyScore: 92,
      description: 'Safest route - Well-lit main streets',
      waypoints: [
        { lat: 37.7749, lng: -122.4194 },
        { lat: 37.7759, lng: -122.4184 },
        { lat: 37.7769, lng: -122.4174 }
      ]
    },
    {
      id: 2,
      duration: '10 min',
      durationMinutes: 10,
      distance: '0.7 mi',
      mode: mode || 'walking',
      safetyScore: 75,
      description: 'Fastest route - Shorter but less populated',
      waypoints: [
        { lat: 37.7749, lng: -122.4194 },
        { lat: 37.7765, lng: -122.4180 },
        { lat: 37.7769, lng: -122.4174 }
      ]
    },
    {
      id: 3,
      duration: '14 min',
      durationMinutes: 14,
      distance: '0.9 mi',
      mode: mode || 'walking',
      safetyScore: 88,
      description: 'Scenic route - Through park with good visibility',
      waypoints: [
        { lat: 37.7749, lng: -122.4194 },
        { lat: 37.7755, lng: -122.4195 },
        { lat: 37.7762, lng: -122.4185 },
        { lat: 37.7769, lng: -122.4174 }
      ]
    }
  ];

  return routes;
};

// Mock Directions
export const generateMockDirections = (routeId) => {
  const directionSets = {
    1: [
      {
        id: 1,
        instruction: 'Head north on Market Street',
        distance: '0.2 mi',
        duration: '3 min',
        maneuver: 'straight',
        safetyNote: null
      },
      {
        id: 2,
        instruction: 'Turn right onto 5th Avenue',
        distance: '0.3 mi',
        duration: '4 min',
        maneuver: 'turn-right',
        safetyNote: 'Well-lit area with shops'
      },
      {
        id: 3,
        instruction: 'Continue straight through intersection',
        distance: '0.1 mi',
        duration: '2 min',
        maneuver: 'straight',
        safetyNote: null
      },
      {
        id: 4,
        instruction: 'Turn left onto Oak Street',
        distance: '0.2 mi',
        duration: '3 min',
        maneuver: 'turn-left',
        safetyNote: null
      },
      {
        id: 5,
        instruction: 'Arrive at destination on your right',
        distance: '0 mi',
        duration: '0 min',
        maneuver: 'arrive',
        safetyNote: null
      }
    ],
    2: [
      {
        id: 1,
        instruction: 'Head northeast on Market Street',
        distance: '0.3 mi',
        duration: '4 min',
        maneuver: 'straight',
        safetyNote: null
      },
      {
        id: 2,
        instruction: 'Turn right onto Cedar Lane',
        distance: '0.2 mi',
        duration: '3 min',
        maneuver: 'turn-right',
        safetyNote: 'Caution: Less populated area'
      },
      {
        id: 3,
        instruction: 'Turn left onto Oak Street',
        distance: '0.2 mi',
        duration: '3 min',
        maneuver: 'turn-left',
        safetyNote: null
      },
      {
        id: 4,
        instruction: 'Arrive at destination on your left',
        distance: '0 mi',
        duration: '0 min',
        maneuver: 'arrive',
        safetyNote: null
      }
    ],
    3: [
      {
        id: 1,
        instruction: 'Head west on Market Street',
        distance: '0.1 mi',
        duration: '2 min',
        maneuver: 'straight',
        safetyNote: null
      },
      {
        id: 2,
        instruction: 'Turn right into Central Park entrance',
        distance: '0.2 mi',
        duration: '3 min',
        maneuver: 'turn-right',
        safetyNote: 'Park area - Good visibility'
      },
      {
        id: 3,
        instruction: 'Follow park path along the main trail',
        distance: '0.3 mi',
        duration: '4 min',
        maneuver: 'straight',
        safetyNote: 'Stay on main path'
      },
      {
        id: 4,
        instruction: 'Exit park onto Pine Street',
        distance: '0.1 mi',
        duration: '2 min',
        maneuver: 'turn-left',
        safetyNote: null
      },
      {
        id: 5,
        instruction: 'Turn right onto Oak Street',
        distance: '0.2 mi',
        duration: '3 min',
        maneuver: 'turn-right',
        safetyNote: null
      },
      {
        id: 6,
        instruction: 'Arrive at destination on your right',
        distance: '0 mi',
        duration: '0 min',
        maneuver: 'arrive',
        safetyNote: null
      }
    ]
  };

  return directionSets[routeId] || directionSets[1];
};

// Incident Type Labels
export const incidentTypeLabels = {
  assault: 'Assault',
  theft: 'Theft',
  harassment: 'Harassment',
  vandalism: 'Vandalism',
  other: 'Other'
};

// Incident Type Colors
export const incidentTypeColors = {
  assault: 'danger',
  theft: 'warning',
  harassment: 'warning',
  vandalism: 'primary',
  other: 'primary'
};

// Travel Mode Icons (text representations)
export const travelModeLabels = {
  walking: 'Walking',
  biking: 'Biking',
  transit: 'Public Transit',
  driving: 'Driving'
};

// Get safety score color
export const getSafetyScoreColor = (score) => {
  if (score >= 85) return '#00AA55';
  if (score >= 70) return '#FFAA00';
  return '#DC3545';
};

// Get safety score label
export const getSafetyScoreLabel = (score) => {
  if (score >= 85) return 'Very Safe';
  if (score >= 70) return 'Moderately Safe';
  return 'Use Caution';
};
