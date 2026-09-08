// <sc-globe> — rotating orthographic globe with real Natural Earth geometry
// and boats running great-circle passages between cruising ports.
//
// Ported from design/globe.js. Geometry, palette, passages and vessel drawing
// are unchanged. Two production changes:
//   1. d3-geo / topojson-client / the Natural Earth atlas are vendored under
//      assets/vendor/ rather than fetched from a third-party CDN at runtime.
//   2. prefers-reduced-motion freezes rotation and vessel motion (WEBSITE_SPEC §6).
//      The globe still renders a full static frame.
(function () {
  const ATLAS = 'assets/vendor/countries-110m.json';

  const OCEAN = 'oklch(0.17 0.05 238)';
  const OCEAN_EDGE = 'oklch(0.25 0.07 215)';
  const LAND = 'oklch(0.35 0.035 215)';
  const LAND_EDGE = 'oklch(0.48 0.04 210)';
  const GRAT = 'oklch(0.70 0.16 200)';
  const ROUTE = 'oklch(0.70 0.16 200)';
  const BOAT = 'oklch(0.80 0.13 85)';

  // Real cruising passages: [from lon,lat], [to lon,lat], speed multiplier, phase
  const PASSAGES = [
    [[-77.35, 25.08], [-75.78, 23.51], 2.0, 0.00],  // Nassau → George Town
    [[-5.35, 36.14], [-61.85, 17.12], 0.42, 0.15],  // Gibraltar → Antigua
    [[-79.55, 8.95], [-139.6, -9.78], 0.34, 0.55],  // Panama → Marquesas
    [[-9.14, 38.72], [-15.6, 28.1], 1.1, 0.35],     // Lisbon → Canaries
    [[-15.6, 28.1], [-23.51, 14.92], 1.0, 0.62],    // Canaries → Cape Verde
    [[2.65, 39.57], [14.51, 35.9], 1.3, 0.08],      // Palma → Malta
    [[16.44, 43.51], [19.92, 39.62], 1.5, 0.44],    // Split → Corfu
    [[27.43, 37.03], [24.03, 35.34], 1.7, 0.72],    // Bodrum → Crete
    [[18.42, -33.92], [-5.71, -15.96], 0.6, 0.70],  // Cape Town → St Helena
    [[31.02, -29.86], [57.5, -20.16], 0.5, 0.28],   // Durban → Mauritius
    [[55.45, -4.62], [39.66, -4.05], 0.8, 0.90],    // Seychelles → Mombasa
    [[73.51, 4.17], [98.4, 7.89], 0.55, 0.20],      // Maldives → Phuket
    [[174.76, -36.85], [178.44, -18.14], 1.2, 0.85], // Auckland → Fiji
    [[-79.55, 8.95], [-90.31, -0.74], 0.9, 0.05],   // Panama → Galápagos
    [[-90.31, -0.74], [-139.6, -9.78], 0.38, 0.48], // Galápagos → Marquesas
    [[-149.57, -17.54], [-151.74, -16.5], 2.0, 0.30], // Tahiti → Bora Bora
    [[-157.86, 21.31], [-139.6, -9.78], 0.45, 0.66], // Honolulu → Marquesas
    [[178.44, -18.14], [168.32, -17.74], 1.3, 0.12], // Fiji → Vanuatu
    [[151.21, -33.87], [166.46, -22.27], 0.8, 0.58], // Sydney → Nouméa
    [[-117.16, 32.72], [-109.91, 22.89], 1.0, 0.78], // San Diego → Cabo
    [[-123.12, 49.28], [-131.65, 55.34], 1.1, 0.40], // Vancouver → Ketchikan
    [[-171.75, -13.83], [-175.2, -21.13], 1.2, 0.92], // Apia → Nuku'alofa
    [[115.74, -32.06], [96.87, -12.19], 0.42, 0.10], // Fremantle → Cocos (Keeling)
    [[115.74, -32.06], [115.22, -8.75], 0.5, 0.55],  // Fremantle → Bali
    [[130.84, -12.46], [123.58, -10.16], 1.1, 0.33], // Darwin → Kupang
    [[151.21, -33.87], [174.76, -36.85], 0.6, 0.18], // Sydney → Auckland
    [[144.79, 13.44], [134.58, 7.5], 0.9, 0.70],     // Guam → Palau
    [[-149.57, -17.54], [-159.78, -21.2], 0.8, 0.86], // Papeete → Rarotonga
    [[103.85, 1.29], [110.34, 1.55], 1.4, 0.24],     // Singapore → Kuching
    [[114.17, 22.3], [120.98, 14.6], 1.0, 0.61],     // Hong Kong → Manila
    [[139.77, 35.68], [127.68, 26.2], 0.8, 0.15],    // Tokyo → Okinawa
    [[72.87, 19.08], [73.51, 4.17], 0.7, 0.47],      // Mumbai → Maldives
    [[55.27, 25.2], [58.4, 23.6], 1.6, 0.80],        // Dubai → Muscat
    [[29.0, 41.0], [23.73, 37.98], 1.4, 0.36],       // Istanbul → Athens
    [[-5.07, 50.15], [-8.4, 43.37], 1.0, 0.68],      // Falmouth → A Coruña
    [[-21.94, 64.15], [5.32, 60.39], 0.6, 0.22],     // Reykjavík → Bergen
    [[-63.57, 44.65], [-52.7, 47.56], 0.9, 0.52],    // Halifax → St John's
    [[-71.31, 41.49], [-64.78, 32.3], 0.8, 0.05],    // Newport → Bermuda
    [[-64.78, 32.3], [-25.67, 37.74], 0.35, 0.74],   // Bermuda → Azores
    [[-61.5, 10.65], [-61.75, 12.05], 2.2, 0.41],    // Trinidad → Grenada
    [[-75.5, 10.4], [-78.9, 9.55], 1.7, 0.88],       // Cartagena → San Blas
    [[18.42, -33.92], [-38.5, -12.97], 0.30, 0.13],  // Cape Town → Salvador
    [[3.4, 6.45], [-4.02, 5.32], 1.0, 0.64],         // Lagos → Abidjan
    [[-71.6, -33.05], [-109.35, -27.11], 0.36, 0.29], // Valparaíso → Easter Island
    [[-68.3, -54.8], [-57.85, -51.7], 0.9, 0.76]     // Ushuaia → Falklands
  ];

  // Frozen frame time. Non-zero so the passages show partial progress and the
  // vessels sit on their routes rather than all bunched at their origins.
  const STILL_T = 42;

  function waitForLibs() {
    return new Promise(resolve => {
      const tick = () => {
        if (window.d3 && window.d3.geoOrthographic && window.topojson) resolve();
        else requestAnimationFrame(tick);
      };
      tick();
    });
  }

  class ScGlobe extends HTMLElement {
    connectedCallback() {
      if (this._booted) return;
      this._booted = true;
      this.style.display = 'block';
      this.style.width = '100%';
      this.style.height = '100%';

      this._canvas = document.createElement('canvas');
      this._canvas.style.cssText = 'display:block;width:100%;height:100%;';
      this._canvas.setAttribute('role', 'presentation');
      this.appendChild(this._canvas);
      this._ctx = this._canvas.getContext('2d');

      this._motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      this._still = this._motionQuery.matches;
      this._onMotionChange = () => {
        this._still = this._motionQuery.matches;
        if (!this._land) return;
        if (this._still) {
          if (this._raf) cancelAnimationFrame(this._raf);
          this._raf = null;
          this._draw(STILL_T);
        } else if (!this._raf) {
          this._start = performance.now();
          this._loop();
        }
      };
      if (this._motionQuery.addEventListener) {
        this._motionQuery.addEventListener('change', this._onMotionChange);
      } else if (this._motionQuery.addListener) {
        this._motionQuery.addListener(this._onMotionChange);
      }

      this._ro = new ResizeObserver(() => {
        this._resize();
        // A frozen globe still has to repaint when the box changes size.
        if (this._still && this._land) this._draw(STILL_T);
      });
      this._ro.observe(this);

      waitForLibs()
        .then(() => fetch(ATLAS).then(r => r.json()))
        .then(topo => {
          this._land = window.topojson.feature(topo, topo.objects.countries);
          this._graticule = window.d3.geoGraticule10();
          this._projection = window.d3.geoOrthographic().clipAngle(90);
          this._path = window.d3.geoPath(this._projection, this._ctx);
          this._routes = PASSAGES.map(p => ({
            interp: window.d3.geoInterpolate(p[0], p[1]),
            from: p[0],
            to: p[1],
            speed: p[2],
            phase: p[3]
          }));
          this._resize();
          this._start = performance.now();
          if (this._still) this._draw(STILL_T);
          else this._loop();
        })
        .catch(() => {
          // Offline / blocked: leave the hero background empty rather than faking geography.
        });
    }

    disconnectedCallback() {
      if (this._ro) this._ro.disconnect();
      if (this._raf) cancelAnimationFrame(this._raf);
      if (this._motionQuery) {
        if (this._motionQuery.removeEventListener) {
          this._motionQuery.removeEventListener('change', this._onMotionChange);
        } else if (this._motionQuery.removeListener) {
          this._motionQuery.removeListener(this._onMotionChange);
        }
      }
    }

    _resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = this.clientWidth || 800;
      const h = this.clientHeight || 600;
      this._w = w;
      this._h = h;
      this._canvas.width = Math.round(w * dpr);
      this._canvas.height = Math.round(h * dpr);
      this._ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (this._projection) {
        // Globe sized generously and anchored right, cropped like a porthole view.
        const r = Math.min(w, h) * 0.62;
        this._r = r;
        this._cx = w * 0.74;
        this._cy = h * 0.5;
        this._projection.scale(r).translate([this._cx, this._cy]);
      }
    }

    _visible(pt) {
      const rot = this._projection.rotate();
      return window.d3.geoDistance(pt, [-rot[0], -rot[1]]) < Math.PI / 2;
    }

    _loop() {
      this._raf = requestAnimationFrame(() => this._loop());
      this._draw((performance.now() - this._start) / 1000);
    }

    _draw(t) {
      const ctx = this._ctx;

      // Slow west-to-east spin, gentle tilt.
      this._projection.rotate([-40 - t * 1.9, -14 + Math.sin(t / 22) * 5, 0]);

      ctx.clearRect(0, 0, this._w, this._h);

      // Ocean sphere
      ctx.beginPath();
      this._path({ type: 'Sphere' });
      const g = ctx.createRadialGradient(
        this._cx - this._r * 0.35, this._cy - this._r * 0.4, this._r * 0.1,
        this._cx, this._cy, this._r
      );
      g.addColorStop(0, OCEAN_EDGE);
      g.addColorStop(1, OCEAN);
      ctx.fillStyle = g;
      ctx.fill();

      // Graticule
      ctx.beginPath();
      this._path(this._graticule);
      ctx.strokeStyle = GRAT;
      ctx.globalAlpha = 0.17;
      ctx.lineWidth = 0.7;
      ctx.stroke();
      ctx.globalAlpha = 1;

      // Land
      ctx.beginPath();
      this._path(this._land);
      ctx.fillStyle = LAND;
      ctx.fill();
      ctx.strokeStyle = LAND_EDGE;
      ctx.lineWidth = 0.6;
      ctx.stroke();

      // Terminator rim
      ctx.beginPath();
      this._path({ type: 'Sphere' });
      ctx.strokeStyle = GRAT;
      ctx.globalAlpha = 0.3;
      ctx.lineWidth = 1.1;
      ctx.stroke();
      ctx.globalAlpha = 1;

      // Passages
      this._routes.forEach(rt => {
        const prog = ((t * 0.045 * rt.speed) + rt.phase) % 1;

        const full = [];
        for (let i = 0; i <= 48; i++) full.push(rt.interp(i / 48));
        ctx.beginPath();
        this._path({ type: 'LineString', coordinates: full });
        ctx.strokeStyle = ROUTE;
        ctx.globalAlpha = 0.18;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 6]);
        ctx.stroke();
        ctx.setLineDash([]);

        const steps = Math.max(2, Math.round(48 * prog));
        const sailed = [];
        for (let i = 0; i <= steps; i++) sailed.push(rt.interp((i / 48)));
        ctx.beginPath();
        this._path({ type: 'LineString', coordinates: sailed });
        ctx.globalAlpha = 0.75;
        ctx.lineWidth = 1.6;
        ctx.stroke();
        ctx.globalAlpha = 1;

        // Port dots — small hollow rings, deliberately unlike the vessels
        [rt.from, rt.to].forEach(p => {
          if (!this._visible(p)) return;
          const xy = this._projection(p);
          ctx.beginPath();
          ctx.arc(xy[0], xy[1], 2.6, 0, Math.PI * 2);
          ctx.strokeStyle = ROUTE;
          ctx.globalAlpha = 0.55;
          ctx.lineWidth = 1.2;
          ctx.stroke();
          ctx.globalAlpha = 1;
        });

        // Vessel — heading-oriented hull with a wake
        const pos = rt.interp(prog);
        if (!this._visible(pos)) return;
        const ahead = rt.interp(Math.min(1, prog + 0.006));
        const xy = this._projection(pos);
        const xyA = this._projection(ahead);
        const heading = Math.atan2(xyA[1] - xy[1], xyA[0] - xy[0]);

        ctx.save();
        ctx.translate(xy[0], xy[1]);
        ctx.rotate(heading);

        // Wake astern
        const wake = ctx.createLinearGradient(-26, 0, 0, 0);
        wake.addColorStop(0, 'oklch(0.80 0.13 85 / 0)');
        wake.addColorStop(1, 'oklch(0.80 0.13 85 / 0.7)');
        ctx.beginPath();
        ctx.moveTo(-26, -2.4);
        ctx.lineTo(0, -0.6);
        ctx.lineTo(0, 0.6);
        ctx.lineTo(-26, 2.4);
        ctx.closePath();
        ctx.fillStyle = wake;
        ctx.fill();

        // Halo so the hull holds up over land
        ctx.beginPath();
        ctx.arc(0, 0, 10.5 + Math.sin(t * 2.2 + rt.phase * 9) * 1.4, 0, Math.PI * 2);
        ctx.fillStyle = BOAT;
        ctx.globalAlpha = 0.18;
        ctx.fill();
        ctx.globalAlpha = 1;

        // Hull — pointed bow, flared sides, squared stern
        ctx.beginPath();
        ctx.moveTo(9.5, 0);
        ctx.quadraticCurveTo(3.5, 4.4, -4.6, 3.5);
        ctx.lineTo(-4.6, -3.5);
        ctx.quadraticCurveTo(3.5, -4.4, 9.5, 0);
        ctx.closePath();
        ctx.fillStyle = BOAT;
        ctx.fill();
        ctx.strokeStyle = 'oklch(0.15 0.035 220 / 0.65)';
        ctx.lineWidth = 0.9;
        ctx.stroke();

        // Cabin — the detail that makes it read as a boat rather than an arrowhead
        ctx.beginPath();
        ctx.moveTo(2.6, 1.9);
        ctx.lineTo(-1.8, 1.9);
        ctx.lineTo(-1.8, -1.9);
        ctx.lineTo(2.6, -1.9);
        ctx.closePath();
        ctx.fillStyle = 'oklch(0.15 0.035 220 / 0.55)';
        ctx.fill();
        ctx.restore();
      });
    }
  }

  if (!window.customElements.get('sc-globe')) {
    window.customElements.define('sc-globe', ScGlobe);
  }
})();
