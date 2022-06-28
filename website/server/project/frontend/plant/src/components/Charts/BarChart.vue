<template>
  <!--
      :settings="{packages: [欲加載的套件]}"
      :data=chartData(欲加載的資料，資料必須是陣列)
      :options=chartOptions(欲加載的選項，例如標題與子標題)
  -->
  <GChart
    :resizeDebounce="500"
    :settings="{packages: ['bar']}"
    :data="chartData"
    :options="chartOptions"
    :createChart="(el, google) => new google.charts.Bar(el)"
     @ready="onChartReady"
  />
</template>
<script>
export default {
  name: 'bar-chart',
  //  props讓父組件可以傳遞參數給子組件
  //  父組件透過引用子組件的參數名稱來傳遞數據，例如chartData:"message"，預設值為空字串
  props: {
    chartData: {
      default: ''
    },
    chartColor: {
      default: ''
    },
    chartHeight: {
      default: ''
    },
    chartWidth: {
      default: ''
    },
    chartTitle: {
      default: ''
    },
    chartSubTitle: {
      default: ''
    }
  },
  data () {
    return {
      chartsLib: null
    }
  },
  computed: {
    chartOptions () {
      //  不等於null，則回傳null值
      if (!this.chartsLib) {
        return null
      }
      //  反之則回傳圖表與其內容
      return this.chartsLib.charts.Bar.convertOptions({
        chart: {
          //  主標題
          title: this.chartTitle,
          //  子標題
          subtitle: this.chartSubTitle
        },
        bars: 'horizontal', //   Required for Material Bar Charts.
        hAxis: {
          minValue: 0
        },
        //  圖表高度
        height: this.chartHeight,
        // width: this.chartWidth,
        //  圖表顏色，引用格式[[''],[''],['']]
        colors: this.chartColor
      }
      )
    }
  },
  methods: {
    onChartReady (chart, google) {
      this.chartsLib = google
    }
  }
}
</script>
