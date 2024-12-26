document.addEventListener('DOMContentLoaded', function () {
    var players = document.querySelectorAll('.video-js');
    players.forEach(function (player) {
        videojs(player);
    });
});
