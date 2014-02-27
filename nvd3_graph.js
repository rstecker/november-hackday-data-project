var only_pre_data = true;
data_groups = _.reduce(pileOfData, function(results, entry){
  if (entry.days_to_sub >= 0) {
    results.sub.push(entry)
  } else if (entry.days_active < 2) {
    results.free_0.push(entry)
  } else if (entry.days_active < 15) {
    results.free_1.push(entry)
  } else {
    results.free_2.push(entry)
  }
  return results;
}, {free_0: [], free_1: [], free_2: [], sub: []});
shapes = ['circle', 'square', 'diamond', 'cross', 'triangle-up', 'triangle-down']


if (true) {
  console.log("Starting chart 1")
  nv.addGraph(function() {
    var chart = nv.models.multiBarChart().x(function(d) { return d.label });
    window.chart = chart;
    var margins = chart.margin();
    margins.left += 20;
    margins.bottom += 50;
    chart.margin(margins);
    chart.xAxis.rotateLabels(-40)
      .tickFormat(function(d) {
        return d;
      });
    chart.yAxis
      .tickFormat(d3.format('%'));
    graph_data = unmodified_values(email_domains);
    d3.select('#chart_1').append("svg")
      .datum(graph_data)
      .transition().call(chart);
    nv.utils.windowResize(chart.update);
    return chart;
  });
  console.log("Finished chart 1")
}
function unmodified_values(func) {
  return [
    {
      key: 'Free 0-1 days',
      values: groupers(data_groups.free_0, func, 0.01)
    },{
      key: 'Free 2-14 days',
      values: groupers(data_groups.free_1, func, 0.01)
    },{
      key: 'Free 15+ days',
      values: groupers(data_groups.free_2, func, 0.01)
    },{
      key: 'Subscriber',
      values: groupers(data_groups.sub, func, 0.01)
    }
  ]
}

function groupers(data, func, show_percent) {
  var results = _.reduce(data, function(results, entry){
    key = func(entry);
    if (!_.isObject(results[key])) {
      results[key] = {
        label: key,
        count: 0.0,
        x: key
      }
    }
    results[key].count += 1;
    return results;
  }, {});

  results = _.reduce(results, function(results, obj) {
    obj.y = obj.count / data.length
    if (obj.y > show_percent) {
      results.push(obj);
    }
    return results;
  }, []);
  return _.values(results);
}

function playlist_avg(data_entry) {
  var list = null;
  if (only_pre_data)
    list = data_entry.playlists_pre_sub.slice()
  else
    list = data_entry.playlists_pre_sub.concat(data_entry.playlists_post_sub)
  var val = list.length;
  if (val != 0) {
    val = _.reduce(list, function(memo, x){
      return memo + x; 
    }, 0.0) / val;
    val = Math.round(Math.round(val)/10.0);
  }
  return val;
}
function playlist_mean(data_entry) {
  var list = null;
  if (only_pre_data)
    list = data_entry.playlists_pre_sub.slice()
  else
    list = data_entry.playlists_pre_sub.concat(data_entry.playlists_post_sub)
  var val = list.length;
  if (val != 0) {
    val = list[val/2 | 0];
  }
  return val;
}
function playlist_count(data_entry) {
  var list = null;
  if (only_pre_data)
    list = data_entry.playlists_pre_sub.slice()
  else
    list = data_entry.playlists_pre_sub.concat(data_entry.playlists_post_sub)
  var val = list.length;
  return val;
}

function reviews_count(data_entry) {
  var val = data_entry.reviews;
  return val;
}
function email_domains(data_entry) {
  var val = data_entry.email_domain;
  return val;
}
function device_counts(data_entry) {
  var val = data_entry.device_count;
  return val;
}
function days_active(data_entry) {
  var val = data_entry.days_active;
  return val;
}
function age(data_entry) {
  var val = data_entry.age;
  return val;
}
function state(data_entry) {
  var val = data_entry.loc_1;
  return val;
}
function city(data_entry) {
  var val = data_entry.loc_0;
  return val;
}
function shares(data_entry) {
  if (only_pre_data)
    return data_entry.shared_pre_sub;
  else
    return data_entry.shared_pre_sub + data_entry.shared_post_sub;
}
function shared_to(data_entry) {
  if (only_pre_data)
    return data_entry.shared_to_pre_sub;
  else
    return data_entry.shared_to_pre_sub + data_entry.shared_to_post_sub;
}
function follower(data_entry) {
  if (only_pre_data)
    return data_entry.follower_1_to_sub + data_entry.follower_day_0;
  else
    return data_entry.follower_1_to_sub + data_entry.follower_day_0 + data_entry.follower_post_sub;
}
function followee(data_entry) {
  if (only_pre_data)
    return data_entry.followee_pre_sub;
  else
    return data_entry.followee_pre_sub + data_entry.followee_post_sub;
}
function days_to_sub(data_entry) {
  var val = data_entry.days_to_sub;
  return val;
}

if (false) {
  console.log("Starting chart 2")
  nv.addGraph(function() {
    var chart = chart = nv.models.scatterChart()
        .showDistX(true)
        .showDistY(true)
        .color(d3.scale.category10().range());
      chart.yAxis.axisLabel('30s+ plays');
      chart.xAxis.tickFormat(function(d){
        return Math.round(Math.pow(10, d))
      }).axisLabel('All Plays (log)');
    d3.select('#chart_2').append("svg")
      .datum(chart_2_data())
      .transition().duration(500).call(chart);
    nv.utils.windowResize(chart.update);
    return chart;
  });
  console.log("Finished chart 2")
}

function chart_2_data() {
  return [
    {
      key: 'Free 0-1 Days',
      values: play_data(data_groups.free_0)
    },{
      key: 'Free 2-14 Days',
      values: play_data(data_groups.free_1)
    },{
      key: 'Free 15+ Days',
      values: play_data(data_groups.free_2)
    },{
      key: 'Subscribers',
      values: play_data(data_groups.sub)
    }
  ]
}

function play_data(data) {
  results = _.filter(data, function(d){
    return d.plays.length > 0
  })
  results = _.reduce(results, function(memo, d){
    _.each(d.plays, function(p) {
      var reducedP = [
        p[0], 
        p[1], 
        (p[2] < 30) ? p[2] : p[2] - p[2]%20,
        p[3] - p[3]%20
      ];
      var key = reducedP.join(" ");
      if (memo[key]) {
        memo[key].size += 2
      } else {
        memo[key] = {
          x: (reducedP[2] == 0)? 0 : Math.log(reducedP[2] + reducedP[0])/Math.LN10,
          y: (reducedP[3] == 0)? 0 : reducedP[3],
          size: 2,
          shape: shapes[reducedP[0]],
          tooltip: " Awesome data goes here!"
        }
      }
    });
    return memo
  }, {});
  return _.values(results)
}


function play_starts(p){
  return p[2];
}
function play_completes(p){
  return p[3];
}
function play_incompletes(p) {
  return p[2] - p[3];
}
function chart_3_play_starts(m) {
  d3.select('#chart_3').append("svg").datum(chart_3_data(m))
  chart.update()
}
if (false) {
  console.log("Starting chart 3")
  nv.addGraph(function() {
    var chart = nv.models.multiBarChart().x(function(d) { return d.label });
    var margins = chart.margin();
    margins.left += 20;
    margins.bottom += 50;
    chart.margin(margins);

    chart.xAxis.rotateLabels(-40)
      .tickFormat(function(d) {
        return d;
      });

    d3.select('#chart_3 svg')
      .datum(chart_3_data(play_incompletes))
      .transition().duration(500).call(chart);
    nv.utils.windowResize(chart.update);
    window.rebChart = chart;
    return chart;    
  });
  console.log("Finished chart 3")
}


function chart_3_data(play_index) {
  results =  [
    {
      key: 'Free 0-1 days',
      values: play_delta(data_groups.free_0, play_index)
    },{
      key: 'Free 2-14 days',
      values: play_delta(data_groups.free_1, play_index)
    },{
      key: 'Free 15+ days',
      values: play_delta(data_groups.free_2, play_index)
    },{
      key: 'Subscriber',
      values: play_delta(data_groups.sub, play_index)
    }
  ]
  console.log(" returning data ",results)
  return results
}


function play_delta(data, play_val_func) {
  results = _.reduce(data, function(results, d) {
    if (d.plays) {
      var set = [0,0,0]
      _.each(d.plays, function(p){
        set[p[0]] += play_val_func(p);
      });
      _.each(set, function(s,i) {
        results[i].push(s);
      });
    }
    return results;
  }, [[],[],[]]);
  var plays_0 = 0
  var plays_0_1 = 0
  var plays_1 = 0
  var plays_1_2 = 0
  var plays_2 = 0
  var entries = results[0].length * 1.0;

  for (var i = 0; i < entries; ++i){
    plays_0 += results[0][i];
    plays_0_1 += results[1][i] - results[0][i];
    plays_1 += results[1][i];
    plays_1_2 += results[2][i] - results[1][i];
    plays_2 += results[2][i];
  }

  return [
    {
      y: plays_0 / (1.0 * entries),
      x: 1,
      label: 'Avg. Day 0'
    },
    {
      y: plays_0_1 / (1.0 * entries),
      x: 2,
      label: 'Avg. Delta Days 0 to 1'
    },
    {
      y: plays_1 / (1.0 * entries),
      x: 2,
      label: 'Avg. Day 1'
    },    
    {
      y: plays_1_2 / (1.0 * entries),
      x: 3,
      label: 'Avg. Delta Days 1 to 2'
    },
    {
      y: plays_2 / (1.0 * entries),
      x: 4,
      label: 'Avg. Play Day 2'
    }
  ]
}
