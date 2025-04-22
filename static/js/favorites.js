function setupFavoriteButtons() {
  document.querySelectorAll('.favorite-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      try {
        const authResponse = await fetch('/auth/user');
        const authData = await authResponse.json();

        if (!authData.authenticated) {
          window.location.href = '/auth/signin';
          return;
        }

        const repoId = btn.dataset.repoId;
        const repoData = JSON.parse(btn.dataset.repo);

        if (btn.classList.contains('active')) {
          await fetch(`/favorites/remove/${repoId}`, { method: 'DELETE' });
          btn.classList.remove('active');
        } else {
          await fetch('/favorites/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              repo_id: repoId,
              repo_data: repoData
            })
          });
          btn.classList.add('active');
        }
      } catch (error) {
        console.error("Error handling favorite:", error);
      }
    });
  });
}

async function markExistingFavorites() {
  try {
    const authResponse = await fetch('/auth/user');
    const authData = await authResponse.json();
    if (!authData.authenticated) return;

    const response = await fetch('/api/favorites');
    if (!response.ok) return;

    const favorites = await response.json();
    const favoriteIds = favorites.map(fav => fav.id);

    document.querySelectorAll('.favorite-btn').forEach(btn => {
      if (favoriteIds.includes(btn.dataset.repoId)) {
        btn.classList.add('active');
      }
    });
  } catch (error) {
    console.error("Error loading favorites:", error);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelectorAll('.favorite-btn').length > 0) {
    setupFavoriteButtons();
    markExistingFavorites();
  }
});