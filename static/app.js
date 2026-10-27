(function () {
  'use strict';

  var MODES = ['Walk', 'Cycle', 'Bus', 'MRT', 'Car'];

  var form = document.getElementById('footprint-form');
  var modeInput = document.getElementById('mode-input');
  var confirmInput = document.getElementById('confirm-high');
  var cta = form ? form.querySelector('.cta') : null;

  var LABELS = {
    distance_km: 'distance',
    aircon_hours: 'air-con hours',
    meat_meals: 'meat meals'
  };

  var PROMPTS = {
    distance_km: 'type how far the trip was, like 5 or 5.5',
    aircon_hours: 'type the hours the air-con was on, like 4',
    meat_meals: 'type the number of meat meals, like 1'
  };

  var LIMITS = { distance_km: 100, aircon_hours: 24, meat_meals: 20 };

  function clearError(field) {
    var slot = document.querySelector('[data-error-for="' + field + '"]');
    var holder = document.querySelector('.field[data-field="' + field + '"]');
    if (slot) { slot.textContent = ''; }
    if (holder) { holder.classList.remove('is-invalid'); }
  }

  function showError(field, message) {
    var slot = document.querySelector('[data-error-for="' + field + '"]');
    var holder = document.querySelector('.field[data-field="' + field + '"]');
    if (slot) { slot.textContent = message; }
    if (holder) { holder.classList.add('is-invalid'); }
  }

  function validateField(field, raw, integer) {
    var text = (raw || '').trim().replace(/,/g, '');
    if (text === '') {
      return 'Oops, the ' + LABELS[field] + ' box is empty — ' + PROMPTS[field] + '.';
    }
    if (integer) {
      if (!/^\d+$/.test(text)) {
        if (/^-\d+$/.test(text)) {
          return 'The number of ' + LABELS[field] + " can't be below zero — put 0 if there were none.";
        }
        if (/^-?\d+\.\d+$/.test(text)) {
          return 'Please use a whole number for ' + LABELS[field] + ' — no halves, like 1 or 2.';
        }
        return "Hmm, I couldn't read that — " + PROMPTS[field] + ". Letters and symbols don't work here.";
      }
    } else if (!/^-?\d*\.?\d+$/.test(text)) {
      return "Hmm, I couldn't read that — " + PROMPTS[field] + ". Letters and symbols don't work here.";
    }

    var value = parseFloat(text);
    if (isNaN(value)) {
      return "Hmm, I couldn't read that — " + PROMPTS[field] + '.';
    }
    if (value < 0) {
      return 'The ' + LABELS[field] + " can't be below zero — put 0 instead.";
    }
    if (value > LIMITS[field]) {
      var unit = field === 'distance_km' ? 'km' : field === 'aircon_hours' ? 'hours' : 'meals';
      return 'That looks like a lot! Please keep the ' + LABELS[field] + ' at ' + LIMITS[field] + ' ' + unit + ' or less.';
    }
    return null;
  }

  /* ---------- transport picker ---------- */
  if (form) {
    var choices = form.querySelectorAll('.choice');
    Array.prototype.forEach.call(choices, function (button) {
      button.addEventListener('click', function () {
        Array.prototype.forEach.call(choices, function (other) {
          other.classList.remove('is-active');
          other.setAttribute('aria-checked', 'false');
        });
        button.classList.add('is-active');
        button.setAttribute('aria-checked', 'true');
        modeInput.value = button.dataset.mode;
        clearError('mode');
      });
    });

    /* ---------- live field checks ---------- */
    ['distance_km', 'aircon_hours', 'meat_meals'].forEach(function (field) {
      var input = document.getElementById(field);
      if (!input) { return; }
      var integer = field !== 'distance_km';
      input.addEventListener('input', function () {
        if (input.value.trim() === '') { clearError(field); return; }
        var message = validateField(field, input.value, integer);
        if (message) { showError(field, message); } else { clearError(field); }
      });
      input.addEventListener('blur', function () {
        var message = validateField(field, input.value, integer);
        if (message) { showError(field, message); } else { clearError(field); }
      });
    });

    /* ---------- reset ---------- */
    var resetButton = document.getElementById('reset-form');
    if (resetButton) {
      resetButton.addEventListener('click', function () {
        ['distance_km', 'aircon_hours', 'meat_meals'].forEach(function (field) {
          var input = document.getElementById(field);
          if (input) { input.value = ''; }
          clearError(field);
        });
        clearError('mode');
        var box = document.getElementById('confirm-high-box');
        if (box) { box.checked = false; }
        if (confirmInput) { confirmInput.value = '0'; }
        var first = document.getElementById('distance_km');
        if (first) { first.focus(); }
      });
    }

    /* ---------- submit as AJAX so nothing reloads on an error ---------- */
    form.addEventListener('submit', function (event) {
      event.preventDefault();

      var firstBad = null;
      [['distance_km', false], ['aircon_hours', true], ['meat_meals', true]].forEach(function (pair) {
        var input = document.getElementById(pair[0]);
        var message = validateField(pair[0], input.value, pair[1]);
        if (message) {
          showError(pair[0], message);
          if (!firstBad) { firstBad = input; }
        } else {
          clearError(pair[0]);
        }
      });

      if (firstBad) {
        firstBad.focus();
        firstBad.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }

      if (cta) { cta.disabled = true; cta.textContent = 'Adding it up…'; }

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'fetch' }
      })
        .then(function (response) { return response.text(); })
        .then(function (html) {
          document.open();
          document.write(html);
          document.close();
        })
        .catch(function () {
          if (cta) { cta.disabled = false; cta.textContent = 'Calculate my footprint'; }
          window.location.reload();
        });
    });
  }

  /* ---------- the Moshi easter egg ---------- */
  var mysteryModal = document.getElementById('mystery-modal');
  var mysteryScroll = document.getElementById('mystery');
  var mysteryConfirm = document.getElementById('mystery-confirm');
  var mysteryCancel = document.getElementById('mystery-cancel');

  if (mysteryModal && mysteryScroll && mysteryScroll.value === '1') {
    mysteryModal.hidden = false;
    if (mysteryConfirm) { mysteryConfirm.focus(); }
  }

  if (mysteryModal) {
    mysteryCancel.addEventListener('click', function () {
      mysteryModal.hidden = true;
      var walk = document.querySelector('.choice[data-mode="Walk"]');
      if (walk) { walk.click(); walk.focus(); }
    });

    mysteryConfirm.addEventListener('click', function () {
      mysteryModal.hidden = true;
      var box = document.getElementById('confirm-high-box');
      if (box) { box.checked = true; }
      if (confirmInput) { confirmInput.value = '1'; }
      form.requestSubmit();
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !mysteryModal.hidden) { mysteryCancel.click(); }
    });
  }

  /* ---------- share card ---------- */
  var shareData = document.getElementById('share-data');
  var canvas = document.getElementById('share-canvas');

  if (shareData && canvas && canvas.getContext) {
    var data = JSON.parse(shareData.textContent);
    var ctx = canvas.getContext('2d');
    var W = canvas.width;
    var H = canvas.height;
    var displayFont = '"Nunito", -apple-system, sans-serif';

    var bg = ctx.createLinearGradient(0, 0, W, H);
    bg.addColorStop(0, '#eafff3');
    bg.addColorStop(0.55, '#e3f6ff');
    bg.addColorStop(1, '#fff9e0');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = 'rgba(46, 204, 113, 0.13)';
    ctx.beginPath();
    ctx.arc(W - 90, 130, 240, 0, Math.PI * 2);
    ctx.fill();

    ctx.textAlign = 'center';

    ctx.font = '170px ' + displayFont;
    ctx.fillText(data.emoji, W / 2, 300);

    ctx.fillStyle = '#14402b';
    ctx.font = '900 58px ' + displayFont;
    ctx.fillText('Green Footprints', W / 2, 400);

    ctx.fillStyle = '#5a7f6a';
    ctx.font = '700 40px ' + displayFont;
    ctx.fillText(data.date_label, W / 2, 460);

    var numberGradient = ctx.createLinearGradient(W / 2 - 200, 0, W / 2 + 200, 0);
    numberGradient.addColorStop(0, '#2ecc71');
    numberGradient.addColorStop(1, '#1b8fd4');
    ctx.fillStyle = numberGradient;
    ctx.font = '900 210px ' + displayFont;
    ctx.fillText(String(data.total), W / 2, 680);

    ctx.fillStyle = '#5a7f6a';
    ctx.font = '700 44px ' + displayFont;
    ctx.fillText('kg of CO2 today', W / 2, 740);

    ctx.fillStyle = '#14402b';
    ctx.font = '900 62px ' + displayFont;
    ctx.fillText(data.headline, W / 2, 850);

    var pills = [];
    if (data.streak > 0) { pills.push('🔥 ' + data.streak + '-day streak'); }
    if (data.saved && data.saved > 0) { pills.push('📉 ' + data.saved + ' kg under my average'); }
    if (!pills.length) { pills.push('🌱 ' + data.points + ' green points'); }

    var pillY = 930;
    pills.forEach(function (label) {
      ctx.font = '900 38px ' + displayFont;
      var width = ctx.measureText(label).width + 80;
      ctx.fillStyle = '#ffffff';
      roundRect(ctx, (W - width) / 2, pillY, width, 78, 39);
      ctx.fill();
      ctx.fillStyle = '#14402b';
      ctx.fillText(label, W / 2, pillY + 52);
      pillY += 100;
    });

    ctx.fillStyle = '#7a9b88';
    ctx.font = '700 34px ' + displayFont;
    ctx.fillText('greenfootprints · made for curious students', W / 2, H - 70);

    function roundRect(c, x, y, w, h, r) {
      c.beginPath();
      c.moveTo(x + r, y);
      c.arcTo(x + w, y, x + w, y + h, r);
      c.arcTo(x + w, y + h, x, y + h, r);
      c.arcTo(x, y + h, x, y, r);
      c.arcTo(x, y, x + w, y, r);
      c.closePath();
    }

    var status = document.getElementById('share-status');

    document.getElementById('download-card').addEventListener('click', function () {
      canvas.toBlob(function (blob) {
        if (!blob) { status.textContent = 'Sorry, the card could not be saved. Try Copy text instead.'; return; }
        var link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'green-footprints-' + data.date_label.replace(/\s+/g, '-') + '.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(function () { URL.revokeObjectURL(link.href); }, 2000);
        status.textContent = 'Card downloaded — share it with a friend! 🌍';
      }, 'image/png');
    });

    document.getElementById('copy-text').addEventListener('click', function () {
      var text = 'My day made ' + data.total + ' kg of CO2 ' + data.emoji + ' ' +
        data.headline + '. ' + data.points + ' green points so far.';
      var done = function () { status.textContent = 'Copied! Paste it anywhere. 📋'; };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { status.textContent = text; });
      } else {
        status.textContent = text;
      }
    });
  }
})();
