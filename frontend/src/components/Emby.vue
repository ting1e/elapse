<template>
    <v-sheet
      class="d-flex align-center justify-center flex-wrap text-center mx-auto px-4 mt-16"
      elevation="4"
      height="300"
      max-width="1200"
      width="100%"
      rounded
    >
    <div><p>Emby daily count</p></div>
  
    <div id="emby" style="height: 200px; width:100%"></div>
    </v-sheet>
</template>
  
  <script setup>

  import {onMounted} from "vue";
  import axios from "axios";
  import * as echarts from 'echarts/core';
import {
  TitleComponent,
  CalendarComponent,
  TooltipComponent,
  VisualMapComponent
} from 'echarts/components';
import { ScatterChart } from 'echarts/charts';
import { UniversalTransition } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  TitleComponent,
  CalendarComponent,
  TooltipComponent,
  VisualMapComponent,
  ScatterChart,
  CanvasRenderer,
  UniversalTransition
]);
      onMounted(() => {
      var chart_ele = document.getElementById("emby")
      var cell_size =  Math.min((chart_ele.clientHeight - 55)/7,(chart_ele.clientWidth - 80)/52)
      let myChart = echarts.init(chart_ele);
      var option;
      let today = new Date();
      var date = new Date(today.getFullYear()-1+'/'+(today.getMonth()+1)+'/'+today.getDate()).getTime();
      var end = new Date().getTime();
      const dayTime = 3600 * 24 * 1000;
      let days=[31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
      // console.log(date)
      
      var daily = []
      for (let time = date; time < end; time += dayTime) {
        daily.push([
        echarts.time.format(time, '{yyyy}-{MM}-{dd}', false),
        0
      ]);
    }
  
  option = {
    tooltip: {
      position: 'top',
      borderWidth :0,
      backgroundColor:'#000',
      padding :[1,5],
      textStyle:{
        color:'#fff',
        fontSize:10,
      },
      formatter: function (p) {
          var out_str = `${p.data[1]} min`
          if (p.data[1] > 60)
          {
            var h = Math.floor(p.data[1]/60)
            var m = p.data[1] % 60
            // console.log(h,m)
            out_str = `${h} h ${m} min`
          }
              return `Played ${out_str} on ${echarts.time.format('yyyy-MM-dd', p.data[0])}`;
          }
    },
    // gradientColor: ['#ebedf0','#9be9a8','#40c463','#30a14e','#216e39',],
  
    grid: {
      show: false,  // 取消显示边框
      borderWidth: 0  // 确保没有边框线
    },
    visualMap: {
      min: 0,
      max: 1440,
      show: false,  // 关闭颜色条
      pieces: [
              {min: 0, max: 0, color: '#ebedf0'},
              {min: 1, max: 60, color: '#9be9a8'},
              {min: 61, max: 180, color: '#40c463'},
              {min: 181, max: 360, color: '#30a14e'},
              {min: 361, max: 1440, color: '#216e39'},
          ]
    },
    calendar: [{
      left:40,
      top:25,
      cellSize: cell_size,
      range: [date, end],
      yearLabel: { show: false },
      monthLabel: {
              nameMap: 'EN',  // 月份使用英文显示
              fontSize:10,
          },
      dayLabel:{
        firstDay: 1, 
        nameMap: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        align:'right',
        fontSize:10,
        // position:'end',
        
      },
      splitLine: {
          show: true,
          lineStyle: {
            color: '#fff',
            // width: 10,
            type: 'solid',
          }
      },
      itemStyle: {
          color: '#fff',
          // borderWidth: 2,
          borderColor: '#fff',
        }
      
    },
    // {
    //   left:1025,
    //   top:25,
    //   cellSize: cell_size,
    //   range: ['2024-07-01', '2024-08-00'],
    //   yearLabel: { show: false },
    //   monthLabel: {
    //           nameMap: 'EN',  // 月份使用英文显示
    //           fontSize:10,
    //       },
    //   dayLabel:{
    //     show:false,
    //     firstDay: 1, 
    //     nameMap: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    //     align:'right',
    //     fontSize:10,
    //     // position:'end',
        
    //   },
    //   splitLine: {
    //       show: true,
    //       lineStyle: {
    //         color: '#fff',
    //         // width: 10,
    //         type: 'solid',
    //       }
    //   },
    //   itemStyle: {
    //       color: '#fff',
    //       // borderWidth: 2,
    //       borderColor: '#fff',
    //     }
      
    // },
  ],
  
    
    series: [{
      calendarIndex: 0,
      type: 'scatter',
      coordinateSystem: 'calendar',
      symbol:'path://M5,0 L15,0 C16.1,0 17,0.9 17,2 L17,13 C17,14.1 16.1,15 15,15 L5,15 C3.9,15 3,14.1 3,13 L3,2 C3,0.9 3.9,0 5,0 Z',
      symbolSize:cell_size *0.8,
      
      data: daily,
    },
    // {
    //   calendarIndex: 1,
    //   type: 'scatter',
    //   coordinateSystem: 'calendar',
    //   symbol:'path://M5,0 L15,0 C16.1,0 17,0.9 17,2 L17,13 C17,14.1 16.1,15 15,15 L5,15 C3.9,15 3,14.1 3,13 L3,2 C3,0.9 3.9,0 5,0 Z',
    //   symbolSize:cell_size *0.8,
    //   data: daily,
    // },
  
  ],
  };
  
  
  option && myChart.setOption(option);
  
  axios.get("/emby_report").then((res) => {
        // console.log(res)
        for(var idx in res.data)
        {
          daily.push([
          res.data[idx][0],
          parseInt(parseInt(res.data[idx][1])/60)
        ])     
        }
        // console.log(daily)
        option.series[0].data =  daily
        // option.series[1].data = daily
        myChart.setOption(option);      
    });
  
  window.onresize = ()=>{
    
    cell_size =  Math.min((chart_ele.clientHeight - 55)/7,(chart_ele.clientWidth - 80)/52)
    option.calendar.cellSize = cell_size
    option.series.symbolSize = cell_size *0.8
    // console.log(cell_size)
    myChart.setOption(option);
    myChart.resize()
  }
  
  })
  
  
  </script>
  