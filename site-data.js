(function () {
  const ORDER = ["venugopal", "satheesan", "chennithala"];

  const CANDIDATES = {
    venugopal: {
      id: "venugopal",
      field: "kc_venugopal",
      name: "K.C. Venugopal",
      short: "Venugopal",
      color: "#c2410c",
      accentClass: "v",
      profilePage: "profile-venugopal.html",
      wikiTitle: "K._C._Venugopal",
      role: "AICC organisation leader | Alappuzha MP",
      positioning: "Organisation-heavy base",
      descriptor: "Organization-first option with a large starting base, but weak tracked-window conversion.",
      scores: { favoring: 48, against: 67, improvement: 82 },
      suggestion: "Move the case from invisible network strength to visible state-level endorsements and a clearer public mandate story.",
      research: [
        "K.C. Venugopal is the AICC general secretary handling organisation and is also a Lok Sabha MP from Alappuzha.[1]",
        "His public resume includes Union ministerial work and three terms as an MLA, giving him strong national-state linkages.[1]"
      ],
      swot: {
        strengths: [
          "Direct access to the national party structure and organisational machinery.",
          "A substantial starting vote base was already visible in the first tracked snapshot."
        ],
        weaknesses: [
          "Added only a small share of newly observed votes during the tracked window.",
          "Live tracker evidence did not support a late-momentum narrative."
        ],
        opportunities: [
          "Can position himself as the option for smoother AICC-state coordination.[4]",
          "May appeal to delegates prioritising internal balance over raw tracker momentum."
        ],
        threats: [
          "A choice that diverges from tracker dominance would need stronger public explanation.",
          "A shrinking share from the opening snapshot leaves little room for an optics-heavy campaign."
        ]
      },
      signals: [
        "Visible district endorsements matter more for him than another insider-heavy pitch.",
        "Any future batch where his capture share moves into double digits would materially improve the data story.",
        "His strongest argument is coherence and coordination, not recent vote-flow momentum."
      ]
    },
    satheesan: {
      id: "satheesan",
      field: "vd_satheesan",
      name: "V.D. Satheesan",
      short: "Satheesan",
      color: "#2563eb",
      accentClass: "s",
      profilePage: "profile-satheesan.html",
      wikiTitle: "V._D._Satheesan",
      role: "Legislative face | Paravur MLA",
      positioning: "Tracked-window frontrunner",
      descriptor: "Tracker leader and mass-facing legislative option.",
      scores: { favoring: 86, against: 29, improvement: 54 },
      suggestion: "Convert observed momentum into a broad legitimacy case while avoiding overclaiming from spike-heavy intervals.",
      research: [
        "V.D. Satheesan represented Paravur from 2001 and served as Kerala's Leader of the Opposition from 2021 to 2026.[2]",
        "His legislative profile gives him the clearest public-facing continuity argument after the UDF win.[2][4]"
      ],
      swot: {
        strengths: [
          "Dominated the tracked window by a very wide margin in both absolute additions and share capture.",
          "Combines a legislative leadership profile with a clear momentum story from the observed data."
        ],
        weaknesses: [
          "Several of the biggest gains arrived in spike intervals, which requires careful caveating.",
          "Front-runner status attracts the strongest scrutiny from rivals and from the party high command."
        ],
        opportunities: [
          "Can argue that both the legislative result and the tracked window point in the same direction.",
          "A Satheesan choice would be easy to frame as mandate alignment after the UDF victory."
        ],
        threats: [
          "If spike-heavy periods dominate the public conversation, critics may question how much of the lead was organic.",
          "Any signs of overconfidence could complicate post-selection faction management."
        ]
      },
      signals: [
        "The data case is strongest when framed around the whole tracked window, not just isolated spikes.",
        "His challenge is no longer visibility; it is building an inclusion-first team narrative.",
        "If he is chosen, the operational question becomes integration rather than justification."
      ]
    },
    chennithala: {
      id: "chennithala",
      field: "ramesh_chennithala",
      name: "Ramesh Chennithala",
      short: "Chennithala",
      color: "#047857",
      accentClass: "c",
      profilePage: "profile-chennithala.html",
      wikiTitle: "Ramesh_Chennithala",
      role: "Veteran reconciler | Haripad MLA",
      positioning: "Veteran consensus pitch",
      descriptor: "Veteran option with long experience and a stable but narrow tracked footprint.",
      scores: { favoring: 34, against: 78, improvement: 88 },
      suggestion: "His route would require a sharper reconciliation story and a clearer reason to privilege experience over live tracker strength.",
      research: [
        "Ramesh Chennithala is a permanent invitee to the Congress Working Committee and a former Kerala Leader of the Opposition.[3]",
        "He also served as KPCC president and later as Kerala Home Minister, giving him the deepest veteran resume in the field.[3]"
      ],
      swot: {
        strengths: [
          "Carries the most extensive institutional memory and faction-management experience among the three contenders.",
          "A veteran profile can still appeal to leaders seeking a reconciliation candidate."
        ],
        weaknesses: [
          "Stayed in a narrow low-share band throughout the tracked window.",
          "Did not translate seniority into observable vote acquisition at anything close to the frontrunner's pace."
        ],
        opportunities: [
          "Could be pitched as a stabiliser if the party values balance, experience and senior mediation.[3][4]",
          "May fit a consensus formula if the final call prioritises internal accommodation over tracker signals."
        ],
        threats: [
          "A low tracked footprint makes a Chennithala selection the hardest to explain through data alone.",
          "He risks being read as backward-looking if the party wants to highlight renewal after victory."
        ]
      },
      signals: [
        "His case improves only if the debate shifts from momentum to stewardship and internal balance.",
        "He needs a stronger why-now argument than either of the other two contenders.",
        "Without that reframing, the tracker leaves him well outside the lead contest."
      ]
    }
  };

  function splitCSVLine(line) {
    const parts = [];
    let current = "";
    let inQuote = false;

    for (let i = 0; i < line.length; i += 1) {
      const character = line[i];
      if (character === '"') {
        inQuote = !inQuote;
        continue;
      }
      if (character === "," && !inQuote) {
        parts.push(current);
        current = "";
        continue;
      }
      current += character;
    }

    parts.push(current);
    return parts;
  }

  function parseInteger(value) {
    const parsed = parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : NaN;
  }

  function parseDecimal(value) {
    const parsed = parseFloat(value);
    return Number.isFinite(parsed) ? parsed : NaN;
  }

  function parseTimestamp(value) {
    const parsed = new Date(String(value || "").replace(" ", "T"));
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function parseDataset(text) {
    const lines = text.trim().split(/\r?\n/);
    if (!lines.length) {
      return { rows: [], events: [] };
    }

    const header = splitCSVLine(lines[0]);
    const rows = [];
    const events = [];

    for (let index = 1; index < lines.length; index += 1) {
      const line = lines[index];
      if (!line.trim()) {
        continue;
      }

      const values = splitCSVLine(line);
      const base = {};
      header.forEach((key, keyIndex) => {
        base[key] = values[keyIndex] || "";
      });

      const timestampDate = parseTimestamp(base.timestamp);
      const alert = String(base.alert || "").trim();
      const totalVotes = parseInteger(base.total_votes);

      if (!Number.isFinite(totalVotes)) {
        if (base.timestamp || alert) {
          events.push({
            timestamp: base.timestamp || "",
            timestampDate,
            alert,
            type: alert.startsWith("ERROR") ? "error" : "note",
            deltaTotal: 0
          });
        }
        continue;
      }

      const row = {
        timestamp: base.timestamp,
        timestampDate,
        total_votes: totalVotes,
        kc_venugopal_votes: parseInteger(base.kc_venugopal_votes) || 0,
        kc_venugopal_pct: parseDecimal(base.kc_venugopal_pct) || 0,
        vd_satheesan_votes: parseInteger(base.vd_satheesan_votes) || 0,
        vd_satheesan_pct: parseDecimal(base.vd_satheesan_pct) || 0,
        ramesh_chennithala_votes: parseInteger(base.ramesh_chennithala_votes) || 0,
        ramesh_chennithala_pct: parseDecimal(base.ramesh_chennithala_pct) || 0,
        delta_total: parseInteger(base.delta_total) || 0,
        delta_kc_venugopal: parseInteger(base.delta_venugopal) || 0,
        delta_vd_satheesan: parseInteger(base.delta_satheesan) || 0,
        delta_ramesh_chennithala: parseInteger(base.delta_chennithala) || 0,
        alert
      };

      rows.push(row);

      if (alert) {
        events.push({
          timestamp: row.timestamp,
          timestampDate: row.timestampDate,
          alert,
          type: alert.startsWith("ERROR") ? "error" : "spike",
          deltaTotal: row.delta_total
        });
      }
    }

    return { rows, events };
  }

  async function loadDataset() {
    const response = await fetch("poll_data.csv", { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Unable to load poll_data.csv");
    }
    const text = await response.text();
    return parseDataset(text);
  }

  function formatNumber(value) {
    if (!Number.isFinite(value)) {
      return "-";
    }
    return value.toLocaleString("en-IN");
  }

  function formatPercent(value, digits) {
    if (!Number.isFinite(value)) {
      return "-";
    }
    return `${value.toFixed(digits == null ? 1 : digits)}%`;
  }

  function formatSigned(value, digits, suffix) {
    if (!Number.isFinite(value)) {
      return "-";
    }
    const fixed = value.toFixed(digits == null ? 1 : digits);
    const prefix = value > 0 ? "+" : "";
    return `${prefix}${fixed}${suffix || ""}`;
  }

  function clamp(minimum, value, maximum) {
    return Math.max(minimum, Math.min(value, maximum));
  }

  function buildRateSeries(rows, windowSize) {
    const labels = [];
    const series = {
      venugopal: [],
      satheesan: [],
      chennithala: []
    };

    const windowLength = windowSize || 5;

    for (let index = windowLength; index < rows.length; index += 1) {
      let validWindow = true;
      let count = 0;
      let sumVen = 0;
      let sumSat = 0;
      let sumChe = 0;

      for (let inner = index - windowLength + 1; inner <= index; inner += 1) {
        const previous = rows[inner - 1];
        const current = rows[inner];
        const gapMinutes = (current.timestampDate - previous.timestampDate) / 60000;
        if (gapMinutes > 5) {
          validWindow = false;
          break;
        }

        sumVen += current.delta_kc_venugopal;
        sumSat += current.delta_vd_satheesan;
        sumChe += current.delta_ramesh_chennithala;
        count += 1;
      }

      if (!validWindow || !count) {
        continue;
      }

      labels.push(rows[index].timestampDate);
      series.venugopal.push(sumVen / count);
      series.satheesan.push(sumSat / count);
      series.chennithala.push(sumChe / count);
    }

    return { labels, series };
  }

  function buildHourlyBuckets(rows) {
    const buckets = new Map();

    for (let index = 1; index < rows.length; index += 1) {
      const current = rows[index];
      const bucketDate = new Date(
        current.timestampDate.getFullYear(),
        current.timestampDate.getMonth(),
        current.timestampDate.getDate(),
        current.timestampDate.getHours()
      );
      const key = bucketDate.toISOString();

      if (!buckets.has(key)) {
        buckets.set(key, {
          key,
          date: bucketDate,
          label: bucketDate.toLocaleString([], {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
          }),
          total: 0,
          venugopal: 0,
          satheesan: 0,
          chennithala: 0,
          count: 0
        });
      }

      const bucket = buckets.get(key);
      bucket.total += current.delta_total;
      bucket.venugopal += current.delta_kc_venugopal;
      bucket.satheesan += current.delta_vd_satheesan;
      bucket.chennithala += current.delta_ramesh_chennithala;
      bucket.count += 1;
    }

    return Array.from(buckets.values()).sort((left, right) => left.date - right.date);
  }

  function buildTimeBands(rows) {
    const buckets = {
      morning: [],
      afternoon: [],
      evening: [],
      night: []
    };

    rows.slice(1).forEach((row) => {
      const hour = row.timestampDate.getHours();
      if (hour >= 7 && hour < 10) {
        buckets.morning.push(row.delta_total);
      } else if (hour >= 12 && hour < 15) {
        buckets.afternoon.push(row.delta_total);
      } else if (hour >= 17 && hour < 20) {
        buckets.evening.push(row.delta_total);
      } else if (hour >= 20 && hour < 23) {
        buckets.night.push(row.delta_total);
      }
    });

    const average = (values) => {
      if (!values.length) {
        return 0;
      }
      return values.reduce((sum, value) => sum + value, 0) / values.length;
    };

    return {
      morning: average(buckets.morning),
      afternoon: average(buckets.afternoon),
      evening: average(buckets.evening),
      night: average(buckets.night)
    };
  }

  function computeAnalytics(dataset) {
    const rows = dataset.rows || [];
    const events = dataset.events || [];
    if (!rows.length) {
      throw new Error("No valid tracking rows found in poll_data.csv");
    }

    const first = rows[0];
    const last = rows[rows.length - 1];
    const captured = {
      total: last.total_votes - first.total_votes
    };
    const currentVotes = {};
    const startVotes = {};
    const finalShare = {};
    const startShare = {};
    const shareChange = {};
    const captureShare = {};

    ORDER.forEach((candidateId) => {
      const candidate = CANDIDATES[candidateId];
      const voteField = `${candidate.field}_votes`;
      const pctField = `${candidate.field}_pct`;
      const delta = last[voteField] - first[voteField];

      startVotes[candidateId] = first[voteField];
      currentVotes[candidateId] = last[voteField];
      startShare[candidateId] = first[pctField];
      finalShare[candidateId] = last[pctField];
      shareChange[candidateId] = finalShare[candidateId] - startShare[candidateId];
      captured[candidateId] = delta;
      captureShare[candidateId] = captured.total > 0 ? (delta / captured.total) * 100 : 0;
    });

    const gaps = [];
    for (let index = 1; index < rows.length; index += 1) {
      const previous = rows[index - 1];
      const current = rows[index];
      const gapMinutes = (current.timestampDate - previous.timestampDate) / 60000;
      if (gapMinutes > 5) {
        gaps.push({
          start: previous.timestamp,
          end: current.timestamp,
          minutes: gapMinutes,
          afterDelta: current.delta_total,
          alert: current.alert || ""
        });
      }
    }

    const hourly = buildHourlyBuckets(rows);
    const rateSeries = buildRateSeries(rows, 5);
    const topSpikes = rows
      .slice(1)
      .slice()
      .sort((left, right) => right.delta_total - left.delta_total)
      .slice(0, 6)
      .map((row) => ({
        timestamp: row.timestamp,
        deltaTotal: row.delta_total,
        deltaVenugopal: row.delta_kc_venugopal,
        deltaSatheesan: row.delta_vd_satheesan,
        deltaChennithala: row.delta_ramesh_chennithala,
        alert: row.alert
      }));

    const validRows = rows.slice(1);
    const middleIndex = Math.floor(validRows.length / 2);
    const earlyRows = validRows.slice(0, middleIndex);
    const lateRows = validRows.slice(middleIndex);

    function summarizeHalf(inputRows) {
      const total = inputRows.reduce((sum, row) => sum + row.delta_total, 0);
      const satheesan = inputRows.reduce((sum, row) => sum + row.delta_vd_satheesan, 0);
      const venugopal = inputRows.reduce((sum, row) => sum + row.delta_kc_venugopal, 0);
      const chennithala = inputRows.reduce((sum, row) => sum + row.delta_ramesh_chennithala, 0);
      return {
        total,
        satheesanShare: total ? (satheesan / total) * 100 : 0,
        venugopalShare: total ? (venugopal / total) * 100 : 0,
        chennithalaShare: total ? (chennithala / total) * 100 : 0
      };
    }

    const zeroDeltaCounts = {
      venugopal: validRows.filter((row) => row.delta_kc_venugopal === 0).length,
      satheesan: validRows.filter((row) => row.delta_vd_satheesan === 0).length,
      chennithala: validRows.filter((row) => row.delta_ramesh_chennithala === 0).length
    };

    const odds = (() => {
      const rawScores = ORDER.map((candidateId) => {
        return finalShare[candidateId] * 0.7 + captureShare[candidateId] * 0.3 + 5;
      });
      const totalScore = rawScores.reduce((sum, value) => sum + value, 0);
      return ORDER.reduce((accumulator, candidateId, index) => {
        accumulator[candidateId] = totalScore ? (rawScores[index] / totalScore) * 100 : 0;
        return accumulator;
      }, {});
    })();

    return {
      rows,
      events,
      first,
      last,
      captured,
      currentVotes,
      startVotes,
      finalShare,
      startShare,
      shareChange,
      captureShare,
      gaps,
      hourly,
      rateSeries,
      timeBands: buildTimeBands(rows),
      topSpikes,
      earlyLate: {
        early: summarizeHalf(earlyRows),
        late: summarizeHalf(lateRows)
      },
      zeroDeltaCounts,
      durationMinutes: (last.timestampDate - first.timestampDate) / 60000,
      averageVotesPerMinute: captured.total / ((last.timestampDate - first.timestampDate) / 60000),
      odds,
      errorEvents: events.filter((event) => event.type === "error"),
      spikeEvents: events.filter((event) => event.type === "spike")
    };
  }

  function getCandidateAnalytics(analytics, candidateId) {
    const candidate = CANDIDATES[candidateId];
    if (!candidate) {
      throw new Error(`Unknown candidate: ${candidateId}`);
    }

    return {
      candidate,
      currentVotes: analytics.currentVotes[candidateId],
      currentShare: analytics.finalShare[candidateId],
      startingVotes: analytics.startVotes[candidateId],
      startingShare: analytics.startShare[candidateId],
      addedVotes: analytics.captured[candidateId],
      captureShare: analytics.captureShare[candidateId],
      shareChange: analytics.shareChange[candidateId],
      odds: analytics.odds[candidateId]
    };
  }

  async function loadWikipediaImage(title) {
    try {
      const response = await fetch(
        `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(title)}&prop=pageimages&pithumbsize=500&format=json&origin=*`
      );
      const data = await response.json();
      const pages = data.query && data.query.pages ? Object.values(data.query.pages) : [];
      return pages[0] && pages[0].thumbnail ? pages[0].thumbnail.source : "";
    } catch (error) {
      return "";
    }
  }

  window.CMTracker = {
    ORDER,
    CANDIDATES,
    loadDataset,
    computeAnalytics,
    getCandidateAnalytics,
    formatNumber,
    formatPercent,
    formatSigned,
    clamp,
    loadWikipediaImage
  };
})();