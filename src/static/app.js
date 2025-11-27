document.addEventListener('DOMContentLoaded', () => {
  const activitiesList = document.getElementById('activities-list');
  const activitySelect = document.getElementById('activity');
  const signupForm = document.getElementById('signup-form');
  const messageEl = document.getElementById('message');
  let activitiesCache = {};

  function showMessage(text, type = 'info') {
    messageEl.textContent = text;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');
  }

  function hideMessage() {
    messageEl.classList.add('hidden');
  }

  function initialsFor(email) {
    const local = String(email).split('@')[0];
    const tokens = local.split(/[._-]+/).filter(Boolean);
    if (tokens.length === 1) {
      return tokens[0].slice(0, 2).toUpperCase();
    }
    return (tokens[0][0] + tokens[1][0]).toUpperCase();
  }

  function renderActivities(activities) {
    activitiesList.innerHTML = '';
    const names = Object.keys(activities).sort((a, b) => a.localeCompare(b));
    names.forEach((name) => {
      const activity = activities[name];

      const card = document.createElement('div');
      card.className = 'activity-card';

      const title = document.createElement('h4');
      title.textContent = name;

      const description = document.createElement('p');
      description.textContent = activity.description;

      const schedule = document.createElement('p');
      schedule.textContent = `Schedule: ${activity.schedule}`;

      const remaining = activity.max_participants - (activity.participants?.length || 0);
      const slots = document.createElement('p');
      slots.textContent = `Slots remaining: ${remaining} / ${activity.max_participants}`;

      const participantsHeading = document.createElement('h5');
      participantsHeading.textContent = 'Participants';

      const participantsList = document.createElement('ul');
      participantsList.className = 'participants';

      if (activity.participants && activity.participants.length > 0) {
        activity.participants.forEach((email) => {
          const li = document.createElement('li');
          li.className = 'participant-item';
          li.dataset.initials = initialsFor(email);
          li.textContent = email;
          participantsList.appendChild(li);
        });
      } else {
        const li = document.createElement('li');
        li.className = 'no-participants';
        li.textContent = 'No participants yet';
        participantsList.appendChild(li);
      }

      card.appendChild(title);
      card.appendChild(description);
      card.appendChild(schedule);
      card.appendChild(slots);
      card.appendChild(participantsHeading);
      card.appendChild(participantsList);

      activitiesList.appendChild(card);
    });
  }

  function populateSelect(activities) {
    activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
    Object.entries(activities).forEach(([name, activity]) => {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = `${name} (${activity.participants?.length || 0} participants)`;
      activitySelect.appendChild(option);
    });
  }

  async function refreshActivities() {
    hideMessage();
    try {
      const res = await fetch('/activities');
      activitiesCache = await res.json();
      renderActivities(activitiesCache);
      populateSelect(activitiesCache);
    } catch (err) {
      showMessage('Unable to load activities. Please try again later.', 'error');
    }
  }

  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideMessage();
    const emailInput = document.getElementById('email');
    const email = emailInput.value.trim();
    const activityName = activitySelect.value;

    if (!email || !activityName) {
      showMessage('Please enter an email and select an activity', 'error');
      return;
    }

    try {
      const url = `/activities/${encodeURIComponent(activityName)}/signup?email=${encodeURIComponent(email)}`;
      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) {
        // Server provided a useful error message in "detail" or "message"
        throw new Error(data.detail || data.message || 'Signup failed');
      }
      showMessage(data.message || `Signed up ${email} for ${activityName}`, 'success');
      emailInput.value = '';

      // Refresh the local activities and UI
      await refreshActivities();
    } catch (err) {
      showMessage(err.message || 'Unable to sign up. Try again.', 'error');
    }
  });

  // Initial load
  refreshActivities();
});
