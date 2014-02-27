var start = {
  question: "All",
  answers: ["All Users"],
  asker: function(d){
    return 0;
  }
}
var start_1day = {
  question: "Active 1+ Day",
  answers: ["Active 1+ Days"],
  asker: function(d){
    if (d.days_active == 0)
      return -1;
    return 0;
  }
}
var start_hasPlayData = {
  question: "Has Play Data",
  answers: ["Has 3 Day Plays"],
  asker: function(d){
    if (d.plays.length > 0)
      return 0;
    return -1;
  }
}
var start_gender = {
  question: "By Gender",
  answers: ["Female","Male"],
  asker: function(d){
    if (d.gender == 'f')
      return 0
    if (d.gender == 'm')
      return 1;
    return -1;
  }
}
var start_age = {
  question: "By Age",
  answers: ["0-17","18-22","23-33","34-49","50+"],
  asker: function(d){
    if (d.age < 18)
      return 0;
    if (d.age < 23)
      return 1;
    if (d.age < 34)
      return 2;
    if (d.age < 50)
      return 3;
    return 4;
  }
}
var selected_start = start;
var selected_start_index = 0;
var all_starts = [start, start_1day, start_gender, start_hasPlayData, start_age]
var end = {
  answers: ["Free < 2 Days", "Free 2-4 14 Days", "Free > 14 Days", "Subscriber"],
  asker: function(d) {
    if (d.days_to_sub >= 0)
      return 3;
    else if (d.days_active > 14)
      return 2;
    else if (d.days_active > 2)
      return 1;
    return 0;
  }
}
var question1 = { 
  question: "Made a Playlist",
  answers: ["No Playlist", "1 Playlist", "2+ Playlists"],
  asker: function(d) {
    if (d.playlists_pre_sub.length == 0)
      return 0
    if (d.playlists_pre_sub.length == 1)
      return 1
    return 2
  }
}
var question2 = { 
  question: "Shared Content?",
  answers: ["Did not share", "Shared"],
  asker: function(d) {
    if (d.shared_pre_sub > 0)
      return 1
    return 0
  }
}
var question3 = { 
  question: "Shared With?",
  answers: ["Not Shared To", "Shared To"],
  asker: function(d) {
    if (d.shared_to_pre_sub > 0)
      return 1
    return 0
  }
}
var question4 = { 
  question: "Followed?",
  answers: ["Did Not Follow", "Followed 1-2", "Followed 3+"],
  asker: function(d) {
    var follower_count = d.follower_day_0 + d.follower_1_to_sub;
    if (follower_count == 0)
      return 0;
    if (follower_count < 3)
      return 1;
    return 2;
  }
}
var question5 = { 
  question: "Was Followed?",
  answers: ["Was Not Followed", "Was Followed"],
  asker: function(d) {
    if (d.followee_pre_sub == 0)
      return 0;
    return 1;
  }
}
var question6 = { 
  question: "Reviewed?",
  answers: ["No Reviews", "1+ Reviews"],
  asker: function(d) {
    if (d.reviews == 0)
      return 0;
    return 1;
  }
}
var question7 = { 
  question: "Device Count?",
  answers: ["0 Devices", "1 Device", "2-3 Devices", "4+ Devices"],
  asker: function(d) {
    if (d.device_count == 0)
      return 0;
    if (d.device_count == 1)
      return 1;
    if (d.device_count < 4)
      return 2;
    return 3;
  }
}
var question8 = { 
  question: "Followed On What Day?",
  answers: ["Did Not Follow", "Day 0 Only", "On More Than Day 0"],
  asker: function(d) {
    if ((d.follower_1_to_sub + d.follower_post_sub) > 0)
      return 2;
    if (d.follower_day_0 > 0)
      return 1;
    return 0;
  }
}
var question9 = { 
  question: "Playlist Length",
  answers: ["No Playlists", "1-5", "6-15","16+"],
  asker: function(d) {
    if (d.playlists_pre_sub.length == 0) {
      return 0;
    }
    var sum = _.reduce(d.playlists_pre_sub, function(memo, x) { return memo + x;}, 0.0);
    var avg = sum / d.playlists_pre_sub.length;
    if (avg < 6) {
      return 1;
    }
    if (avg < 16) {
      return 2;
    }
    return 3;
  }
}
var all_questions = [question1, question2, question3, question4, question5, question6, question7, question8, question9];
var questions_asked = [question1, question2];
var getEnergyFromPileOfData = function() {
  console.log("Asking ",_.pluck(questions_asked, 'question'));
  return askAndAnswerQuestions(pileOfData, selected_start, questions_asked, end)
}
var askAndAnswerQuestions = function(users, start, questions, end) {
  users = _.filter(users, function(u){
    if (start.asker(u) == -1)
      return false;
    return true;
  })
  s.totalUsers = _.keys(users).length;
  var nodes = [];
  addNodesAndSetNodeBase(nodes, start);
  _.each(questions, function(q){
    console.log("\t"+q.question);
    addNodesAndSetNodeBase(nodes, q);
  });
  addNodesAndSetNodeBase(nodes, end);
  var answers = {}
  _.each(users, function(u){
    var answer = askQuestionsOfUser(u, start, questions, end);
    var key = answer.join("_")
    if (_.isObject(answers[key])) {
      answers[key].count += 1;
    } else {
      answers[key] = { answer: answer, count: 1}
    }
  });
  var links = [];
  _.each(answers, function(a, key) {
    links.push(makeLink(a.answer[0], a.answer[1], a.count, key));
    for (var i = 1; i < a.answer.length - 1; ++i) {
      links.push(makeLink(a.answer[i], a.answer[i+1], a.count, key));
    }
  });
  return { nodes: nodes, links: links}
}

var addNodesAndSetNodeBase = function(nodes, question) {
  question.base = nodes.length;
  _.each(question.answers, function(a) {
    nodes.push({name: a})
  });
}
var ask = function(user, question) {
  return question.base + question.asker(user);
}
var makeLink = function(source, target, value, reb) {
  return { 
      source: source,
      target: target,
      value: value,
      reb: reb
    }
}
var askQuestionsOfUser = function(user, start, listOfQuestions, end) {
  var path = [];
  path.push(ask(user, start));
  _.each(listOfQuestions, function(q){
    path.push(ask(user, q));
  });
  path.push(ask(user, end));
  return path;
}










function drawSankeyGraph(energy) {
  var link = s.svg.append("g").selectAll(".link")
    .data(energy.links)
  .enter().append("path")
    .attr("class", function(d) {
      return "link path_"+d.reb;
    })
    .attr("data-flow", function(d){
      return d.reb;
    })
    .attr("d", s.path)
    .style("stroke-width", function(d) { 
      return Math.max(1, d.dy); 
    })
    .sort(function(a, b) { 
      return a.dy - b.dy; 
    });

  link.append("title")
    .text(function(d) { 
      return s.format(d.value); 
    });

  var node = s.svg.append("g").selectAll(".node")
    .data(energy.nodes)
  .enter().append("g")
    .attr("class", "node")
    .attr("data-flow", function(d){
      var rebs = [];
      _.each(d.sourceLinks, function(l){
        rebs.push(l.reb);
      });
      _.each(d.targetLinks, function(l){
        rebs.push(l.reb);
      });
      return _.uniq(rebs).join(",");
    })
    .attr("data-node", function(d,i){
      return i;
    })
    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
  .call(d3.behavior.drag()
    .origin(function(d) { return d; })
    );

  node.append("rect")
    .attr("height", function(d) { return d.dy; })
    .attr("width", s.sankey.nodeWidth())
    .style("fill", function(d) { 
      return d.color = s.color(d.name.replace(/ .*/, "")); 
    })
    .style("stroke", function(d) { 
      return d3.rgb(d.color).darker(2); 
    })
  .append("title")
    .text(function(d) { 
      return d.name + "\n" + s.format(d.value); 
    });

  node.append("text")
    .attr("class", "node-text")
    .attr("x", -6)
    .attr("y", function(d) { return d.dy / 2; })
    .attr("dy", ".35em")
    .attr("text-anchor", "end")
    .attr("transform", null)
    .text(function(d) { return d.name; })
  .filter(function(d) { return d.x < width / 2; })
    .attr("x", 6 + s.sankey.nodeWidth())
    .attr("text-anchor", "start");
}

function dragmove(d) {
  d3.select(this).attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
  s.sankey.relayout();
  link.attr("d", s.path);
}
s = {}
function sankeyInit() {
  var margin = {top: 20, right: 1, bottom: 6, left: 1},
    width = 1060 - margin.left - margin.right,
    height = 600 - margin.top - margin.bottom;

  s.formatNumber = d3.format(",.0f");
  s.format = function(d) { return s.formatNumber(d) + " users ("+d3.format("%")(d/s.totalUsers)+")" },
  s.color = d3.scale.category20();

  s.svg = d3.select("#flow_1").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  s.sankey = d3.sankey()
    .nodeWidth(15)
    .nodePadding(10)
    .size([width, height]);

  s.path = s.sankey.link();

}

drawGraph = function(energy){
  console.log("Beginning map drawing [nodes "+energy.nodes.length+", links "+energy.links.length+"]");

  s.svg.selectAll('.node').remove();
  s.svg.selectAll('.link').remove();
  s.sankey
    .nodes(energy.nodes)
    .links(energy.links)
    .layout(32);
  drawSankeyGraph(energy);

  $('.link').hover(function(e) {
      var c = $(e.target).attr('data-flow');
      s.svg.selectAll(".path_"+c).classed('active_link', true);
    }, function(e) {
      var c = $(e.target).attr('data-flow');
      s.svg.selectAll(".path_"+c).classed('active_link', false);
    }
  )
  $('.node').hover(function(e){
      var paths = $(e.target).parent().attr('data-flow').split(",");
      _.each(paths, function(p){
        s.svg.selectAll(".path_"+p).classed('active_link', true);
      })
      nodeKey = "_"+$(e.target).parent().data('node')+"_";
      var nodes = s.svg.selectAll(".node-text").text(function(d) { 
        var total = 0;
        var selected = 0;
        _.each(d.sourceLinks, function(l){
          total += l.value;
          if (("_"+l.reb+"_").indexOf(nodeKey) != -1) {
            selected += l.value;
          }
        });
        _.each(d.targetLinks, function(l){
          total += l.value;
          if (("_"+l.reb+"_").indexOf(nodeKey) != -1) {
            selected += l.value;
          }
        });
        return d.name +" ("+d3.format("%")(selected/total)+" of "+d3.format("%")(selected/s.totalUsers)+")";
      })
    }, function(e){
      var paths = $(e.target).parent().attr('data-flow').split(",");
      _.each(paths, function(p){
        s.svg.selectAll(".path_"+p).classed('active_link', false);
      })
      var nodes = s.svg.selectAll(".node-text").text(function(d) { 
        return d.name; 
      })
    }
  )
  console.log("Finished drawing map")
}
drawGraph = _.debounce(drawGraph, 2)


